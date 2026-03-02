<?php
// This file is part of Moodle - http://moodle.org/
//
// Web Service function: local_sectionedit_import_questions
//
// Imports questions from a file (Aiken .txt or Moodle XML .xml) into the
// question bank of a course.  Uses Moodle's built-in qformat_* classes
// to parse and persist the questions.
//
// Replaces the non-existent qbank_importquestions_import_questions WS function.
//
// @package    local_sectionedit
// @copyright  2025 Moodle Automator
// @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later

namespace local_sectionedit\external;

defined('MOODLE_INTERNAL') || die();

use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_single_structure;
use core_external\external_value;

/**
 * External function to import questions into the question bank.
 */
class import_questions extends external_api {

    /**
     * Describe input parameters.
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'courseid' => new external_value(
                PARAM_INT,
                'The course ID (used for context validation)'
            ),
            'categoryid' => new external_value(
                PARAM_INT,
                'Target question category ID in the question bank'
            ),
            'format' => new external_value(
                PARAM_ALPHA,
                'Import format: "xml" (Moodle XML) or "aiken" (Aiken plain-text)'
            ),
            'filecontent' => new external_value(
                PARAM_RAW,
                'Base64-encoded file content (UTF-8 text)'
            ),
        ]);
    }

    /**
     * Execute: import questions from a file into the question bank.
     *
     * @param int    $courseid
     * @param int    $categoryid
     * @param string $format
     * @param string $filecontent  Base64-encoded
     * @return array
     */
    public static function execute(
        int    $courseid,
        int    $categoryid,
        string $format,
        string $filecontent
    ): array {
        global $DB, $CFG, $USER;

        require_once($CFG->dirroot . '/question/format.php');
        require_once($CFG->dirroot . '/question/editlib.php');

        // ── 1. Validate parameters ──────────────────────────────────
        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid'    => $courseid,
            'categoryid'  => $categoryid,
            'format'      => $format,
            'filecontent' => $filecontent,
        ]);

        $courseid    = $params['courseid'];
        $categoryid  = $params['categoryid'];
        $format      = strtolower(trim($params['format']));
        $filecontent = $params['filecontent'];

        // ── 2. Validate format ──────────────────────────────────────
        $allowedformats = ['xml', 'aiken'];
        if (!in_array($format, $allowedformats, true)) {
            throw new \invalid_parameter_exception(
                "Unsupported format '{$format}'. Allowed formats: " .
                implode(', ', $allowedformats)
            );
        }

        // ── 3. Load the question-format class ───────────────────────
        $formatfile = $CFG->dirroot . '/question/format/' . $format . '/format.php';
        if (!file_exists($formatfile)) {
            throw new \moodle_exception(
                'errorgeneral', 'error', '', null,
                "Question format plugin '{$format}' is not installed on this Moodle instance."
            );
        }
        require_once($formatfile);

        $classname = 'qformat_' . $format;
        if (!class_exists($classname)) {
            throw new \moodle_exception(
                'errorgeneral', 'error', '', null,
                "Class '{$classname}' not found after including {$formatfile}."
            );
        }

        // ── 4. Validate course, category, and capabilities ──────────
        $course   = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
        $category = $DB->get_record('question_categories', ['id' => $categoryid], '*', MUST_EXIST);

        $context = \context::instance_by_id($category->contextid);
        self::validate_context($context);
        require_capability('moodle/question:add', $context);

        // ── 5. Decode base64 content ────────────────────────────────
        $rawcontent = base64_decode($filecontent, true);
        if ($rawcontent === false) {
            throw new \invalid_parameter_exception(
                'The filecontent parameter is not valid base64.'
            );
        }

        // ── 6. Snapshot: count questions BEFORE import ──────────────
        $countbefore = (int) $DB->count_records('question_bank_entries', [
            'questioncategoryid' => $categoryid,
        ]);

        // ── 7. Write decoded content to a temp file ─────────────────
        $tmpdir  = make_temp_directory('local_sectionedit_import');
        $ext     = ($format === 'aiken') ? '.txt' : '.xml';
        $tmpfile = $tmpdir . '/' . uniqid('qimport_') . $ext;
        file_put_contents($tmpfile, $rawcontent);

        // ── 8. Configure the format instance ────────────────────────
        $qformat = new $classname();
        $qformat->setCategory($category);
        $qformat->setContexts([$context]);
        $qformat->setCourse($course);
        $qformat->setFilename($tmpfile);
        $qformat->setMatchgrades('nearest');
        $qformat->setCatfromfile(false);
        $qformat->setContextfromfile(false);
        $qformat->setStoponerror(false);

        // ── 9. Run import (buffer output to prevent HTML leaking) ───
        ob_start();
        try {
            $success = $qformat->importprocess();
        } catch (\Exception $e) {
            ob_end_clean();
            @unlink($tmpfile);
            throw new \moodle_exception(
                'errorgeneral', 'error', '', null,
                "Import failed with exception: " . $e->getMessage()
            );
        }
        ob_end_clean();

        // ── 10. Clean up temp file ──────────────────────────────────
        @unlink($tmpfile);

        // ── 11. Count questions AFTER import ────────────────────────
        $countafter = (int) $DB->count_records('question_bank_entries', [
            'questioncategoryid' => $categoryid,
        ]);
        $imported = $countafter - $countbefore;

        // ── 12. Return result ───────────────────────────────────────
        if ($success) {
            $message = "Successfully imported {$imported} question(s) into category '{$category->name}'.";
        } else {
            $message = 'Import failed. Please check that the file content is valid ' .
                       $format . ' format and encoded in UTF-8.';
        }

        return [
            'success'        => (bool) $success,
            'total_imported' => $imported,
            'message'        => $message,
        ];
    }

    /**
     * Describe return values.
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'success'        => new external_value(PARAM_BOOL, 'True if import was successful'),
            'total_imported' => new external_value(PARAM_INT,  'Number of questions imported'),
            'message'        => new external_value(PARAM_TEXT, 'Result message'),
        ]);
    }
}
