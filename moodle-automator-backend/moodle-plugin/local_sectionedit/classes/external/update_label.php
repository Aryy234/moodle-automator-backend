<?php
// This file is part of Moodle - http://moodle.org/
//
// Web Service function: local_sectionedit_update_label
//
// Updates the HTML content (intro) of an existing label (Text and media area).
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
 * External function to update the content of an existing label module.
 */
class update_label extends external_api {

    /**
     * Describe input parameters.
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'labelid' => new external_value(
                PARAM_INT,
                'The instance ID of the label (mdl_label.id)'
            ),
            'content' => new external_value(
                PARAM_RAW,
                'New HTML content for the label'
            ),
        ]);
    }

    /**
     * Execute: update the intro field of an existing label.
     *
     * @param int    $labelid   Instance ID from mdl_label
     * @param string $content   New HTML content
     * @return array
     */
    public static function execute(int $labelid, string $content): array {
        global $DB;

        // 1. Validate parameters.
        $params = self::validate_parameters(self::execute_parameters(), [
            'labelid' => $labelid,
            'content' => $content,
        ]);
        $labelid = $params['labelid'];
        $content = $params['content'];

        // 2. Load the label record and verify it exists.
        $label = $DB->get_record('label', ['id' => $labelid], '*', MUST_EXIST);

        // 3. Check capability on the course context.
        $context = \context_course::instance($label->course);
        self::validate_context($context);
        require_capability('moodle/course:manageactivities', $context);

        // 4. Update the label content.
        $label->intro        = $content;
        $label->introformat  = FORMAT_HTML;
        $label->timemodified = time();
        $DB->update_record('label', $label);

        // 5. Purge course cache so the change appears immediately.
        \course_modinfo::purge_course_cache($label->course);

        return [
            'status'  => true,
            'labelid' => (int) $labelid,
            'message' => 'Label updated successfully.',
        ];
    }

    /**
     * Describe return values.
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'status'  => new external_value(PARAM_BOOL, 'True on success'),
            'labelid' => new external_value(PARAM_INT,  'Instance ID of the updated label'),
            'message' => new external_value(PARAM_TEXT, 'Status message'),
        ]);
    }
}
