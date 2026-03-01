<?php
// This file is part of Moodle - http://moodle.org/
//
// Web Service function: local_sectionedit_add_label_to_section
//
// Creates a new label (Text and media area) module inside a course section.
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
 * External function to add a label module to a course section.
 */
class add_label_to_section extends external_api {

    /**
     * Describe input parameters.
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'courseid' => new external_value(
                PARAM_INT,
                'The id of the course'
            ),
            'sectionid' => new external_value(
                PARAM_INT,
                'The id of the course section (mdl_course_sections.id)'
            ),
            'content' => new external_value(
                PARAM_RAW,
                'HTML content for the label'
            ),
            'name' => new external_value(
                PARAM_TEXT,
                'Optional name/title for the label (for internal identification)',
                VALUE_DEFAULT,
                ''
            ),
        ]);
    }

    /**
     * Execute: create a label module in the specified section.
     *
     * @param int    $courseid
     * @param int    $sectionid
     * @param string $content
     * @param string $name
     * @return array
     */
    public static function execute(int $courseid, int $sectionid, string $content, string $name = ''): array {
        global $DB, $CFG;

        require_once($CFG->dirroot . '/course/modlib.php');
        require_once($CFG->dirroot . '/mod/label/lib.php');

        // 1. Validate parameters.
        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid'  => $courseid,
            'sectionid' => $sectionid,
            'content'   => $content,
            'name'      => $name,
        ]);
        $courseid  = $params['courseid'];
        $sectionid = $params['sectionid'];
        $content   = $params['content'];
        $name      = $params['name'];

        // 2. Load course and check capability.
        $course  = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
        $section = $DB->get_record('course_sections', ['id' => $sectionid, 'course' => $courseid], '*', MUST_EXIST);

        $context = \context_course::instance($courseid);
        self::validate_context($context);
        require_capability('moodle/course:manageactivities', $context);

        // 3. Find the label module type.
        $module = $DB->get_record('modules', ['name' => 'label'], '*', MUST_EXIST);

        // 4. Build the label record.
        $label = new \stdClass();
        $label->course         = $courseid;
        $label->name           = $name ?: 'Contenido';
        $label->intro          = $content;
        $label->introformat    = FORMAT_HTML;
        $label->timemodified   = time();

        // 5. Insert into mdl_label.
        $label->id = $DB->insert_record('label', $label);

        // 6. Determine sort order (add at end of section).
        $maxorder = $DB->get_field('course_modules', 'MAX(deletioninprogress)', ['course' => $courseid]) ?? 0;
        $visible_modules = $DB->get_records('course_modules', [
            'course'  => $courseid,
            'section' => $section->id,
        ], 'added DESC', 'id', 0, 1);
        $neworder = count($visible_modules) + 1;

        // 7. Create the course_module entry.
        $cm = new \stdClass();
        $cm->course     = $courseid;
        $cm->module     = $module->id;
        $cm->instance   = $label->id;
        $cm->section    = $section->id;
        $cm->visible    = 1;
        $cm->added      = time();
        $cm->score      = 0;
        $cm->indent     = 0;
        $cm->completion = 0;
        $cmid = $DB->insert_record('course_modules', $cm);

        // 8. Append cmid to the section's sequence.
        $sequence = $section->sequence ? explode(',', $section->sequence) : [];
        $sequence[] = $cmid;
        $DB->set_field('course_sections', 'sequence', implode(',', $sequence), ['id' => $sectionid]);

        // 9. Purge course cache so the new label appears immediately.
        \course_modinfo::purge_course_cache($courseid);

        return [
            'status'  => true,
            'cmid'    => (int) $cmid,
            'message' => 'Label module created successfully.',
        ];
    }

    /**
     * Describe return values.
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'status'  => new external_value(PARAM_BOOL, 'True on success'),
            'cmid'    => new external_value(PARAM_INT,  'Course module ID of the new label'),
            'message' => new external_value(PARAM_TEXT, 'Status message'),
        ]);
    }
}
