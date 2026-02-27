<?php
// This file is part of Moodle - http://moodle.org/
//
// Web Service function: local_sectionedit_update_section_summary
//
// Updates mdl_course_sections.summary for a given section id.
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
 * External function to update a course-section summary.
 */
class update_section_summary extends external_api {

    /**
     * Describe input parameters.
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'sectionid' => new external_value(
                PARAM_INT,
                'The id of the course section (mdl_course_sections.id)'
            ),
            'summary' => new external_value(
                PARAM_RAW,
                'New HTML content for the section summary'
            ),
            'summaryformat' => new external_value(
                PARAM_INT,
                'Format of the summary (1 = HTML, 0 = MOODLE, 2 = PLAIN, 4 = MARKDOWN)',
                VALUE_DEFAULT,
                1
            ),
        ]);
    }

    /**
     * Execute: update the section summary.
     *
     * @param int    $sectionid
     * @param string $summary
     * @param int    $summaryformat
     * @return array
     */
    public static function execute(int $sectionid, string $summary, int $summaryformat = 1): array {
        global $DB;

        // 1. Validate parameters.
        $params = self::validate_parameters(self::execute_parameters(), [
            'sectionid'     => $sectionid,
            'summary'       => $summary,
            'summaryformat' => $summaryformat,
        ]);
        $sectionid     = $params['sectionid'];
        $summary       = $params['summary'];
        $summaryformat = $params['summaryformat'];

        // 2. Load the section row and its course.
        $section = $DB->get_record('course_sections', ['id' => $sectionid], '*', MUST_EXIST);
        $course  = $DB->get_record('course', ['id' => $section->course], '*', MUST_EXIST);

        // 3. Context & capability check.
        $context = \context_course::instance($course->id);
        self::validate_context($context);
        require_capability('moodle/course:update', $context);

        // 4. Update the record.
        $section->summary       = $summary;
        $section->summaryformat = $summaryformat;
        $section->timemodified  = time();
        $DB->update_record('course_sections', $section);

        // 5. Purge course cache so Moodle shows the new content immediately.
        \course_modinfo::purge_course_cache($course->id);

        // 6. Trigger event so other plugins / logs stay in sync.
        $event = \core\event\course_section_updated::create([
            'objectid' => $section->id,
            'courseid' => $course->id,
            'context'  => $context,
            'other'    => [
                'sectionnum' => $section->section,
            ],
        ]);
        $event->trigger();

        return [
            'status'  => true,
            'message' => 'Section summary updated successfully.',
        ];
    }

    /**
     * Describe return values.
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'status'  => new external_value(PARAM_BOOL, 'True on success'),
            'message' => new external_value(PARAM_TEXT, 'Status message'),
        ]);
    }
}
