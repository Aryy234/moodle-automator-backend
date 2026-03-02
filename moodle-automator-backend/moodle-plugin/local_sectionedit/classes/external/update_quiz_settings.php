<?php
// This file is part of Moodle - http://moodle.org/
//
// Web Service function: local_sectionedit_update_quiz_settings
//
// Updates quiz settings such as time limit.
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
 * External function to update quiz settings (e.g. time limit).
 */
class update_quiz_settings extends external_api {

    /**
     * Describe input parameters.
     */
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'courseid' => new external_value(
                PARAM_INT,
                'The course ID'
            ),
            'cmid' => new external_value(
                PARAM_INT,
                'Course Module ID of the quiz activity'
            ),
            'timelimit' => new external_value(
                PARAM_INT,
                'Time limit in seconds (0 = no limit)',
                VALUE_DEFAULT,
                0
            ),
        ]);
    }

    /**
     * Execute: update quiz settings.
     *
     * @param int $courseid
     * @param int $cmid
     * @param int $timelimit
     * @return array
     */
    public static function execute(
        int $courseid,
        int $cmid,
        int $timelimit = 0
    ): array {
        global $DB, $CFG;

        // ── 1. Validate parameters ──────────────────────────────────
        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid'  => $courseid,
            'cmid'      => $cmid,
            'timelimit' => $timelimit,
        ]);

        $courseid  = $params['courseid'];
        $cmid      = $params['cmid'];
        $timelimit = max(0, $params['timelimit']); // no negatives

        // ── 2. Load course, quiz, and check capabilities ────────────
        $course = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
        $cm     = $DB->get_record('course_modules', ['id' => $cmid, 'course' => $courseid], '*', MUST_EXIST);
        $quiz   = $DB->get_record('quiz', ['id' => $cm->instance], '*', MUST_EXIST);

        $context = \context_module::instance($cmid);
        self::validate_context($context);
        require_capability('mod/quiz:manage', $context);

        // ── 3. Update settings ──────────────────────────────────────
        $updated_fields = [];

        if ($quiz->timelimit !== $timelimit) {
            $DB->set_field('quiz', 'timelimit', $timelimit, ['id' => $quiz->id]);
            $updated_fields[] = 'timelimit';
        }

        // ── 4. Purge caches and trigger event ───────────────────────
        \course_modinfo::purge_course_cache($courseid);

        // Format time limit for human-readable message.
        if ($timelimit > 0) {
            $hours   = intdiv($timelimit, 3600);
            $minutes = intdiv($timelimit % 3600, 60);
            $seconds = $timelimit % 60;
            $parts   = [];
            if ($hours > 0) {
                $parts[] = "{$hours}h";
            }
            if ($minutes > 0) {
                $parts[] = "{$minutes}m";
            }
            if ($seconds > 0) {
                $parts[] = "{$seconds}s";
            }
            $timelimit_str = implode(' ', $parts);
        } else {
            $timelimit_str = 'no limit';
        }

        $message = count($updated_fields) > 0
            ? "Quiz '{$quiz->name}' updated. Time limit: {$timelimit_str}."
            : "No changes needed for quiz '{$quiz->name}'. Time limit already: {$timelimit_str}.";

        return [
            'success'        => true,
            'quiz_name'      => $quiz->name,
            'timelimit'      => $timelimit,
            'timelimit_display' => $timelimit_str,
            'message'        => $message,
        ];
    }

    /**
     * Describe return values.
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'success'           => new external_value(PARAM_BOOL, 'True on success'),
            'quiz_name'         => new external_value(PARAM_TEXT, 'Name of the quiz'),
            'timelimit'         => new external_value(PARAM_INT,  'Time limit in seconds'),
            'timelimit_display' => new external_value(PARAM_TEXT, 'Human-readable time limit'),
            'message'           => new external_value(PARAM_TEXT, 'Result message'),
        ]);
    }
}
