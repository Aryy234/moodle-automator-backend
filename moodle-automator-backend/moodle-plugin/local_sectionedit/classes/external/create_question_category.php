<?php
// This file is part of Moodle - http://moodle.org/
//
// Web Service function: local_sectionedit_create_question_category
//
// Creates a new question category in the question bank.
// Supports two modes:
//   - Course-level (default): creates in context_course.
//   - Module-level: if cmid is provided, creates in that quiz's context_module.
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
 * External function to create a question category in a course or quiz module.
 */
class create_question_category extends external_api {

    /**
     * Describe input parameters.
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'courseid' => new external_value(
                PARAM_INT,
                'The course ID'
            ),
            'name' => new external_value(
                PARAM_TEXT,
                'Name of the new category'
            ),
            'info' => new external_value(
                PARAM_RAW,
                'Description of the category',
                VALUE_DEFAULT,
                ''
            ),
            'cmid' => new external_value(
                PARAM_INT,
                'Optional Course Module ID of a quiz. If provided, the category is ' .
                'created in that module context instead of the course context.',
                VALUE_DEFAULT,
                0
            ),
        ]);
    }

    /**
     * Execute: create a question category.
     *
     * @param int    $courseid
     * @param string $name
     * @param string $info
     * @param int    $cmid
     * @return array
     */
    public static function execute(int $courseid, string $name, string $info = '', int $cmid = 0): array {
        global $DB, $CFG;

        // 1. Validate parameters.
        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'name'     => $name,
            'info'     => $info,
            'cmid'     => $cmid,
        ]);
        $courseid = $params['courseid'];
        $name     = $params['name'];
        $info     = $params['info'];
        $cmid     = $params['cmid'];

        // 2. Load course and determine target context.
        $course = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
        $coursecontext = \context_course::instance($courseid);
        self::validate_context($coursecontext);

        if ($cmid > 0) {
            // Module-level context.
            $cm = $DB->get_record('course_modules', ['id' => $cmid, 'course' => $courseid], '*', MUST_EXIST);
            $context = \context_module::instance($cmid);
        } else {
            // Course-level context.
            $context = $coursecontext;
        }

        require_capability('moodle/question:managecategory', $context);

        // 3. Get or create the invisible top-level category for this context.
        //    We do this manually because question_get_top_category() in Moodle 5.x
        //    may set idnumber = null, which causes dmlwriteexception.
        $topcategory = $DB->get_record('question_categories', [
            'contextid' => $context->id,
            'parent'    => 0,
        ]);
        if (!$topcategory) {
            $top = new \stdClass();
            $top->name       = 'top';
            $top->info       = '';
            $top->infoformat = FORMAT_HTML;
            $top->contextid  = $context->id;
            $top->parent     = 0;
            $top->sortorder  = 0;
            $top->stamp      = make_unique_id_code();
            $top->idnumber   = '';
            $top->id = $DB->insert_record('question_categories', $top);
            $topcategory = $top;
        }
        $parentid = $topcategory->id;

        // 4. Create the new category.
        $category = new \stdClass();
        $category->parent     = $parentid;
        $category->contextid  = $context->id;
        $category->name       = $name;
        $category->info       = $info;
        $category->infoformat = FORMAT_HTML;
        $category->sortorder  = 999;
        $category->stamp      = make_unique_id_code();
        $category->idnumber   = '';

        $category->id = $DB->insert_record('question_categories', $category);

        // Determine context level label.
        $contextlevel = ($context instanceof \context_module) ? 'module' : 'course';

        return [
            'success'      => true,
            'id'           => (int) $category->id,
            'name'         => $category->name,
            'contextid'    => (int) $context->id,
            'contextlevel' => $contextlevel,
            'parent'       => (int) $parentid,
            'message'      => "Category '{$category->name}' created successfully in {$contextlevel} context.",
        ];
    }

    /**
     * Describe return values.
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'success'      => new external_value(PARAM_BOOL, 'True on success'),
            'id'           => new external_value(PARAM_INT,  'New category ID'),
            'name'         => new external_value(PARAM_TEXT, 'Category name'),
            'contextid'    => new external_value(PARAM_INT,  'Context ID'),
            'contextlevel' => new external_value(PARAM_ALPHA, '"course" or "module"'),
            'parent'       => new external_value(PARAM_INT,  'Parent category ID'),
            'message'      => new external_value(PARAM_TEXT, 'Status message'),
        ]);
    }
}
