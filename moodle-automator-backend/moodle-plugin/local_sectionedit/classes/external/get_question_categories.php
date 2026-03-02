<?php
// This file is part of Moodle - http://moodle.org/
//
// Web Service function: local_sectionedit_get_question_categories
//
// Returns question categories for a course.  Supports three modes:
//   1) Course-level (default): categories from context_course only.
//   2) Module-level: if cmid is provided, categories from that quiz
//      module's context_module.
//   3) All: if includeall = true, categories from the course context
//      PLUS all quiz module contexts in the course.
//
// @package    local_sectionedit
// @copyright  2025 Moodle Automator
// @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later

namespace local_sectionedit\external;

defined('MOODLE_INTERNAL') || die();

use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_single_structure;
use core_external\external_multiple_structure;
use core_external\external_value;

/**
 * External function to list question categories for a course (or a specific quiz module).
 */
class get_question_categories extends external_api {

    /**
     * Describe input parameters.
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'courseid' => new external_value(
                PARAM_INT,
                'The course ID to get question categories for'
            ),
            'cmid' => new external_value(
                PARAM_INT,
                'Optional Course Module ID of a quiz. If provided, returns categories ' .
                'from that module context instead of the course context.',
                VALUE_DEFAULT,
                0
            ),
            'includeall' => new external_value(
                PARAM_BOOL,
                'If true, return categories from BOTH the course context AND all quiz ' .
                'module contexts in the course.  Ignores cmid when true.',
                VALUE_DEFAULT,
                false
            ),
        ]);
    }

    /**
     * Execute: return question categories.
     *
     * @param int  $courseid
     * @param int  $cmid
     * @param bool $includeall
     * @return array
     */
    public static function execute(int $courseid, int $cmid = 0, bool $includeall = false): array {
        global $DB, $CFG;

        require_once($CFG->dirroot . '/question/editlib.php');
        require_once($CFG->libdir . '/questionlib.php');

        // 1. Validate parameters.
        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid'   => $courseid,
            'cmid'       => $cmid,
            'includeall' => $includeall,
        ]);
        $courseid   = $params['courseid'];
        $cmid       = $params['cmid'];
        $includeall = $params['includeall'];

        // 2. Load course and base capability check.
        $course = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
        $coursecontext = \context_course::instance($courseid);
        self::validate_context($coursecontext);
        require_capability('moodle/question:viewall', $coursecontext);

        // 3. Collect context IDs to search.
        $contextids = [];

        if ($includeall) {
            // Course context.
            $contextids[] = $coursecontext->id;
            // All quiz module contexts in this course.
            $quizmodules = $DB->get_records_sql(
                "SELECT cm.id
                   FROM {course_modules} cm
                   JOIN {modules} m ON m.id = cm.module AND m.name = 'quiz'
                  WHERE cm.course = :courseid",
                ['courseid' => $courseid]
            );
            foreach ($quizmodules as $qm) {
                $modcontext = \context_module::instance($qm->id, IGNORE_MISSING);
                if ($modcontext) {
                    $contextids[] = $modcontext->id;
                }
            }
        } else if ($cmid > 0) {
            // Specific module context.
            $cm = $DB->get_record('course_modules', ['id' => $cmid, 'course' => $courseid], '*', MUST_EXIST);
            $modcontext = \context_module::instance($cmid);
            $contextids[] = $modcontext->id;
        } else {
            // Course context only (default).
            $contextids[] = $coursecontext->id;
        }

        // 4. Ensure each context has its top category + a visible default child.
        foreach ($contextids as $ctxid) {
            // Get or create the invisible top-level category manually
            // (question_get_top_category may fail in Moodle 5.x with dmlwriteexception
            //  because it sets idnumber = null).
            $topcategory = $DB->get_record('question_categories', [
                'contextid' => $ctxid,
                'parent'    => 0,
            ]);
            if (!$topcategory) {
                $top = new \stdClass();
                $top->name       = 'top';
                $top->info       = '';
                $top->infoformat = FORMAT_HTML;
                $top->contextid  = $ctxid;
                $top->parent     = 0;
                $top->sortorder  = 0;
                $top->stamp      = make_unique_id_code();
                $top->idnumber   = '';
                $top->id = $DB->insert_record('question_categories', $top);
                $topcategory = $top;
            }

            $childcount = $DB->count_records_select(
                'question_categories',
                'contextid = :ctx AND parent = :parent',
                ['ctx' => $ctxid, 'parent' => $topcategory->id]
            );
            if ($childcount == 0) {
                // Determine a friendly name for the default category.
                $ctx = \context::instance_by_id($ctxid);
                if ($ctx instanceof \context_module) {
                    $cm = $DB->get_record('course_modules', ['id' => $ctx->instanceid]);
                    $quiz = $cm ? $DB->get_record('quiz', ['id' => $cm->instance]) : null;
                    $catname = get_string('defaultfor', 'question', $quiz ? $quiz->name : 'Module');
                } else {
                    $catname = get_string('defaultfor', 'question', $course->fullname);
                }
                $default = new \stdClass();
                $default->parent     = $topcategory->id;
                $default->contextid  = $ctxid;
                $default->name       = $catname;
                $default->info       = '';
                $default->infoformat = FORMAT_HTML;
                $default->sortorder  = 999;
                $default->stamp      = make_unique_id_code();
                $default->idnumber   = '';
                $default->id = $DB->insert_record('question_categories', $default);
            }
        }

        // 5. Fetch categories from all collected contexts, excluding top (invisible parent=0).
        if (empty($contextids)) {
            $records = [];
        } else {
            list($insql, $inparams) = $DB->get_in_or_equal($contextids, SQL_PARAMS_NAMED, 'ctx');
            $records = $DB->get_records_select(
                'question_categories',
                "contextid {$insql} AND parent != 0",
                $inparams,
                'contextid, sortorder, name'
            );
        }

        // 6. Build response.
        $categories = [];
        foreach ($records as $record) {
            $questioncount = (int) $DB->count_records('question_bank_entries', [
                'questioncategoryid' => $record->id,
            ]);

            // Label: "course" or "module" so the frontend knows the scope.
            $ctx = \context::instance_by_id($record->contextid, IGNORE_MISSING);
            $contextlevel = '';
            if ($ctx instanceof \context_course) {
                $contextlevel = 'course';
            } else if ($ctx instanceof \context_module) {
                $contextlevel = 'module';
            }

            $categories[] = [
                'id'            => (int) $record->id,
                'name'          => $record->name,
                'info'          => $record->info ?? '',
                'contextid'     => (int) $record->contextid,
                'contextlevel'  => $contextlevel,
                'parent'        => (int) $record->parent,
                'questioncount' => $questioncount,
            ];
        }

        return [
            'course_id'  => $courseid,
            'categories' => $categories,
            'total'      => count($categories),
        ];
    }

    /**
     * Describe return values.
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'course_id' => new external_value(PARAM_INT, 'Course ID'),
            'categories' => new external_multiple_structure(
                new external_single_structure([
                    'id'            => new external_value(PARAM_INT, 'Category ID'),
                    'name'          => new external_value(PARAM_TEXT, 'Category name'),
                    'info'          => new external_value(PARAM_RAW, 'Category description'),
                    'contextid'     => new external_value(PARAM_INT, 'Context ID'),
                    'contextlevel'  => new external_value(PARAM_ALPHA, '"course" or "module"'),
                    'parent'        => new external_value(PARAM_INT, 'Parent category ID (0 = top level)'),
                    'questioncount' => new external_value(PARAM_INT, 'Number of questions in this category'),
                ])
            ),
            'total' => new external_value(PARAM_INT, 'Total number of categories'),
        ]);
    }
}
