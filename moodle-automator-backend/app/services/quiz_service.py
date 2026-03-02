"""
Quiz Service — Lógica de negocio para importación de cuestionarios.

Responsabilidades:
- Parsear archivos en formato Aiken y Moodle XML
- Generar Moodle XML a partir de preguntas parseadas
- Orquestar la importación de preguntas al banco de Moodle
- Proveer preview sin enviar a Moodle
"""

import re
import xml.etree.ElementTree as ET
from typing import Optional, List, Tuple
from html import escape as html_escape

from app.integration.moodle_client import MoodleClient, get_moodle_client, MoodleAPIError
from app.schemas.quiz import (
    ImportFormat,
    ParsedOption,
    ParsedQuestion,
    QuestionType,
    QuizImportResponse,
)


# ==================== PARSERS ====================


def parse_aiken(content: str) -> List[ParsedQuestion]:
    """
    Parsea un archivo en formato Aiken.

    Formato Aiken (solo opción múltiple):
        ¿Pregunta?
        A. Opción 1
        B. Opción 2
        C. Opción 3
        D. Opción 4
        ANSWER: B

    Args:
        content: Contenido del archivo de texto

    Returns:
        Lista de preguntas parseadas
    """
    questions: List[ParsedQuestion] = []
    lines = content.strip().splitlines()

    current_question_text = ""
    current_options: List[Tuple[str, str]] = []  # (letra, texto)
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # Detectar línea ANSWER
        answer_match = re.match(r"^ANSWER:\s*([A-Z])\s*$", line, re.IGNORECASE)

        if answer_match:
            # Construir la pregunta
            correct_letter = answer_match.group(1).upper()

            if current_question_text and current_options:
                options = []
                correct_answer_text = ""

                for letter, text in current_options:
                    is_correct = letter.upper() == correct_letter
                    options.append(ParsedOption(
                        text=text,
                        is_correct=is_correct,
                    ))
                    if is_correct:
                        correct_answer_text = text

                # Generar nombre si no tiene
                name = current_question_text[:80]
                if len(current_question_text) > 80:
                    name = name[:77] + "..."

                questions.append(ParsedQuestion(
                    question_text=current_question_text,
                    question_type=QuestionType.MULTICHOICE,
                    options=options,
                    correct_answer=correct_answer_text,
                    name=name,
                ))

            # Reset
            current_question_text = ""
            current_options = []
            i += 1
            continue

        # Detectar opción (A. texto, B) texto, etc.)
        option_match = re.match(r"^([A-Z])[.)]\s*(.+)$", line, re.IGNORECASE)

        if option_match and current_question_text:
            letter = option_match.group(1)
            text = option_match.group(2).strip()
            current_options.append((letter, text))
            i += 1
            continue

        # Si no es opción ni ANSWER, es parte del enunciado
        if current_options:
            # Ya teníamos opciones, esto es una nueva pregunta
            # (caso raro: pregunta sin ANSWER, la ignoramos)
            current_question_text = line
            current_options = []
        elif current_question_text:
            # Continuar el enunciado (pregunta multilínea)
            current_question_text += " " + line
        else:
            current_question_text = line

        i += 1

    return questions


def parse_moodle_xml(content: str) -> List[ParsedQuestion]:
    """
    Parsea un archivo en formato Moodle XML.

    Soporta los tipos: multichoice, truefalse, shortanswer, essay.

    Args:
        content: Contenido XML del archivo

    Returns:
        Lista de preguntas parseadas
    """
    questions: List[ParsedQuestion] = []

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        raise ValueError(f"Error al parsear XML: {e}")

    for q_element in root.findall(".//question"):
        q_type_attr = q_element.get("type", "")

        # Ignorar categorías y otros elementos no-pregunta
        if q_type_attr in ("category", ""):
            continue

        # Mapear tipo de Moodle a nuestro enum
        type_map = {
            "multichoice": QuestionType.MULTICHOICE,
            "truefalse": QuestionType.TRUEFALSE,
            "shortanswer": QuestionType.SHORTANSWER,
            "essay": QuestionType.ESSAY,
            "numerical": QuestionType.NUMERICAL,
            "matching": QuestionType.MATCHING,
        }

        question_type = type_map.get(q_type_attr)
        if question_type is None:
            # Tipo no soportado, saltar
            continue

        # Extraer nombre
        name_el = q_element.find("name/text")
        name = name_el.text.strip() if name_el is not None and name_el.text else None

        # Extraer enunciado
        qtext_el = q_element.find("questiontext/text")
        question_text = ""
        if qtext_el is not None and qtext_el.text:
            question_text = qtext_el.text.strip()

        if not question_text:
            continue

        # Extraer retroalimentación general
        gf_el = q_element.find("generalfeedback/text")
        general_feedback = gf_el.text.strip() if gf_el is not None and gf_el.text else None

        # Extraer puntuación
        grade_el = q_element.find("defaultgrade")
        default_grade = float(grade_el.text) if grade_el is not None and grade_el.text else 1.0

        # Extraer penalización
        penalty_el = q_element.find("penalty")
        penalty = float(penalty_el.text) if penalty_el is not None and penalty_el.text else 0.3333333

        # Extraer opciones/respuestas
        options: List[ParsedOption] = []
        correct_answer = None

        for answer_el in q_element.findall("answer"):
            fraction = float(answer_el.get("fraction", "0"))
            ans_text_el = answer_el.find("text")
            ans_text = ans_text_el.text.strip() if ans_text_el is not None and ans_text_el.text else ""

            fb_el = answer_el.find("feedback/text")
            feedback = fb_el.text.strip() if fb_el is not None and fb_el.text else None

            is_correct = fraction > 0

            options.append(ParsedOption(
                text=ans_text,
                is_correct=is_correct,
                feedback=feedback,
            ))

            if is_correct and correct_answer is None:
                correct_answer = ans_text

        questions.append(ParsedQuestion(
            question_text=question_text,
            question_type=question_type,
            options=options,
            correct_answer=correct_answer,
            default_grade=default_grade,
            penalty=penalty,
            general_feedback=general_feedback,
            name=name,
        ))

    return questions


# ==================== XML GENERATOR ====================


def questions_to_moodle_xml(
    questions: List[ParsedQuestion],
    category_name: Optional[str] = None,
) -> str:
    """
    Convierte una lista de ParsedQuestion a formato Moodle XML
    para importar al banco de preguntas.

    Args:
        questions: Preguntas a convertir
        category_name: Nombre de la categoría (opcional, se incluye como header)

    Returns:
        String XML en formato Moodle
    """
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<quiz>"]

    # Agregar categoría si se especifica
    if category_name:
        lines.append("  <question type=\"category\">")
        lines.append("    <category>")
        lines.append(f"      <text>$course$/{html_escape(category_name)}</text>")
        lines.append("    </category>")
        lines.append("  </question>")

    for q in questions:
        q_type = q.question_type.value
        q_name = html_escape(q.name or q.question_text[:80])

        lines.append(f'  <question type="{q_type}">')
        lines.append("    <name>")
        lines.append(f"      <text>{q_name}</text>")
        lines.append("    </name>")
        lines.append('    <questiontext format="html">')
        lines.append(f"      <text><![CDATA[{q.question_text}]]></text>")
        lines.append("    </questiontext>")

        if q.general_feedback:
            lines.append('    <generalfeedback format="html">')
            lines.append(f"      <text><![CDATA[{q.general_feedback}]]></text>")
            lines.append("    </generalfeedback>")

        lines.append(f"    <defaultgrade>{q.default_grade}</defaultgrade>")
        lines.append(f"    <penalty>{q.penalty}</penalty>")

        # Escribir opciones
        if q.question_type == QuestionType.MULTICHOICE:
            lines.append("    <single>true</single>")
            lines.append("    <shuffleanswers>1</shuffleanswers>")
            lines.append('    <answernumbering>abc</answernumbering>')

            for opt in q.options:
                fraction = "100" if opt.is_correct else "0"
                lines.append(f'    <answer fraction="{fraction}" format="html">')
                lines.append(f"      <text><![CDATA[{opt.text}]]></text>")
                if opt.feedback:
                    lines.append('      <feedback format="html">')
                    lines.append(f"        <text><![CDATA[{opt.feedback}]]></text>")
                    lines.append("      </feedback>")
                lines.append("    </answer>")

        elif q.question_type == QuestionType.TRUEFALSE:
            for opt in q.options:
                fraction = "100" if opt.is_correct else "0"
                lines.append(f'    <answer fraction="{fraction}" format="moodle_auto_format">')
                lines.append(f"      <text>{html_escape(opt.text)}</text>")
                lines.append("    </answer>")

        elif q.question_type == QuestionType.SHORTANSWER:
            for opt in q.options:
                fraction = "100" if opt.is_correct else "0"
                lines.append(f'    <answer fraction="{fraction}" format="moodle_auto_format">')
                lines.append(f"      <text>{html_escape(opt.text)}</text>")
                lines.append("    </answer>")

        elif q.question_type == QuestionType.ESSAY:
            lines.append('    <responseformat>editor</responseformat>')
            lines.append('    <responserequired>1</responserequired>')

        lines.append("  </question>")

    lines.append("</quiz>")
    return "\n".join(lines)


# ==================== SERVICE CLASS ====================


class QuizService:
    """
    Servicio de importación de cuestionarios.

    Orquesta el parseo de archivos, generación de XML,
    y la comunicación con Moodle para crear preguntas.
    """

    def __init__(self, moodle_client: Optional[MoodleClient] = None):
        self.moodle = moodle_client or get_moodle_client()

    async def get_quiz_activities(self, course_id: int) -> list:
        """Obtiene las actividades cuestionario de un curso desde Moodle."""
        return await self.moodle.get_quizzes_by_course(course_id)

    async def get_question_categories(
        self, course_id: int, cmid: int = 0, include_all: bool = False
    ) -> list:
        """Obtiene las categorías de preguntas de un curso (o de un quiz específico)."""
        return await self.moodle.get_question_categories(
            course_id, cmid=cmid, include_all=include_all
        )

    async def create_category(
        self, course_id: int, name: str, info: str = "", cmid: int = 0
    ) -> dict:
        """Crea una nueva categoría de preguntas."""
        return await self.moodle.create_question_category(course_id, name, info, cmid=cmid)

    async def configure_quiz_questions(
        self,
        course_id: int,
        cmid: int,
        category_id: int,
        mode: str = "all",
        num_questions: int = 10,
        include_subcategories: bool = False,
    ) -> dict:
        """Agrega preguntas de una categoría a un cuestionario."""
        return await self.moodle.configure_quiz_questions(
            course_id=course_id,
            cmid=cmid,
            category_id=category_id,
            mode=mode,
            num_questions=num_questions,
            include_subcategories=include_subcategories,
        )

    async def update_quiz_settings(
        self,
        course_id: int,
        cmid: int,
        time_limit: int = 0,
    ) -> dict:
        """Actualiza los ajustes de un cuestionario (tiempo límite, etc.)."""
        return await self.moodle.update_quiz_settings(
            course_id=course_id,
            cmid=cmid,
            time_limit=time_limit,
        )

    def parse_file(
        self, content: str, format: ImportFormat
    ) -> List[ParsedQuestion]:
        """
        Parsea el contenido de un archivo según su formato.

        Args:
            content: Contenido del archivo como texto
            format: Formato del archivo (aiken | xml)

        Returns:
            Lista de preguntas parseadas

        Raises:
            ValueError: Si el formato no es soportado o el archivo es inválido
        """
        if format == ImportFormat.AIKEN:
            return parse_aiken(content)
        elif format == ImportFormat.XML:
            return parse_moodle_xml(content)
        else:
            raise ValueError(f"Formato no soportado: {format}")

    async def preview_import(
        self,
        content: str,
        format: ImportFormat,
    ) -> QuizImportResponse:
        """
        Parsea un archivo y retorna las preguntas sin enviarlas a Moodle.

        Args:
            content: Contenido del archivo
            format: Formato del archivo

        Returns:
            QuizImportResponse con las preguntas parseadas
        """
        try:
            questions = self.parse_file(content, format)
        except ValueError as e:
            return QuizImportResponse(
                success=False,
                course_id=0,
                format_used=format.value,
                message=f"Error al parsear el archivo: {e}",
                errors=[str(e)],
            )

        return QuizImportResponse(
            success=True,
            course_id=0,
            format_used=format.value,
            total_questions_parsed=len(questions),
            total_questions_imported=0,
            questions=questions,
            message=f"Preview: {len(questions)} preguntas parseadas del archivo ({format.value})",
        )

    async def import_questions(
        self,
        course_id: int,
        category_id: int,
        content: str,
        format: ImportFormat,
        category_name: Optional[str] = None,
    ) -> QuizImportResponse:
        """
        Importa preguntas desde un archivo al banco de preguntas de Moodle.

        Flujo:
        1. Parsear el archivo según su formato
        2. Convertir a Moodle XML (si no lo es ya)
        3. Enviar a Moodle vía API

        Args:
            course_id: ID del curso en Moodle
            category_id: ID de la categoría destino en el banco de preguntas
            content: Contenido del archivo
            format: Formato del archivo
            category_name: Nombre de la categoría (para metadata en XML)

        Returns:
            QuizImportResponse con el resultado
        """
        errors: List[str] = []

        # 1. Parsear
        try:
            questions = self.parse_file(content, format)
        except ValueError as e:
            return QuizImportResponse(
                success=False,
                course_id=course_id,
                format_used=format.value,
                message=f"Error al parsear el archivo: {e}",
                errors=[str(e)],
            )

        if not questions:
            return QuizImportResponse(
                success=False,
                course_id=course_id,
                format_used=format.value,
                message="No se encontraron preguntas válidas en el archivo.",
                errors=["El archivo no contiene preguntas en el formato esperado."],
            )

        # 2. Si el contenido ya es XML válido y viene en formato XML, usarlo directo
        if format == ImportFormat.XML:
            xml_content = content
        else:
            # Convertir preguntas parseadas a Moodle XML
            xml_content = questions_to_moodle_xml(questions, category_name)

        # 3. Enviar a Moodle
        try:
            result = await self.moodle.import_questions_xml(
                course_id=course_id,
                category_id=category_id,
                xml_content=xml_content,
            )
            print(f"✅ Importación exitosa: {len(questions)} preguntas al curso {course_id}")
        except MoodleAPIError as e:
            return QuizImportResponse(
                success=False,
                course_id=course_id,
                format_used=format.value,
                total_questions_parsed=len(questions),
                message=f"Error al importar a Moodle: {e.message}",
                errors=[e.message],
            )

        return QuizImportResponse(
            success=True,
            course_id=course_id,
            category_name=category_name,
            format_used=format.value,
            total_questions_parsed=len(questions),
            total_questions_imported=len(questions),
            message=f"Se importaron {len(questions)} preguntas correctamente al banco de preguntas.",
            errors=errors,
        )


# ==================== SINGLETON ====================

_quiz_service: Optional[QuizService] = None


def get_quiz_service() -> QuizService:
    """Obtiene la instancia global del servicio de quizzes."""
    global _quiz_service
    if _quiz_service is None:
        _quiz_service = QuizService()
    return _quiz_service
