<?php
// This file is part of Moodle - http://moodle.org/
//
// Web Service function: local_sectionedit_configure_quiz_questions
//
// Adds questions from a question bank category to a quiz.
// Two modes:
//   - 'all': adds every question from the category as fixed slots.
//   - 'random': adds N random-question references that pull from the category.
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
 * External function to add questions to a quiz from a category.
 */
class configure_quiz_questions extends external_api {

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
            'categoryid' => new external_value(
                PARAM_INT,
                'Question category ID to pull questions from'
            ),
            'mode' => new external_value(
                PARAM_ALPHA,
                'Mode: "all" (add all questions) or "random" (add random references)',
                VALUE_DEFAULT,
                'all'
            ),
            'numquestions' => new external_value(
                PARAM_INT,
                'Number of random questions to add (only used when mode = "random")',
                VALUE_DEFAULT,
                10
            ),
            'includesubcategories' => new external_value(
                PARAM_BOOL,
                'Whether to include subcategories when using random mode',
                VALUE_DEFAULT,
                false
            ),
        ]);
    }

    /**
     * Execute: add questions to a quiz.
     *
     * @param int    $courseid
     * @param int    $cmid
     * @param int    $categoryid
     * @param string $mode
     * @param int    $numquestions
     * @param bool   $includesubcategories
     * @return array
     */
    public static function execute(
        int    $courseid,
        int    $cmid,
        int    $categoryid,
        string $mode = 'all',
        int    $numquestions = 10,
        bool   $includesubcategories = false
    ): array {
        global $DB, $CFG;

        require_once($CFG->dirroot . '/mod/quiz/locallib.php');

        // ── 1. Validate parameters ──────────────────────────────────
        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid'              => $courseid,
            'cmid'                  => $cmid,
            'categoryid'            => $categoryid,
            'mode'                  => $mode,
            'numquestions'           => $numquestions,
            'includesubcategories'  => $includesubcategories,
        ]);

        $courseid             = $params['courseid'];
        $cmid                 = $params['cmid'];
        $categoryid           = $params['categoryid'];
        $mode                 = strtolower(trim($params['mode']));
        $numquestions          = $params['numquestions'];
        $includesubcategories = $params['includesubcategories'];

        if (!in_array($mode, ['all', 'random'], true)) {
            throw new \invalid_parameter_exception(
                "Invalid mode '{$mode}'. Must be 'all' or 'random'."
            );
        }

        // ── 2. Load course, quiz, and check capabilities ────────────
        $course   = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
        $cm       = $DB->get_record('course_modules', ['id' => $cmid, 'course' => $courseid], '*', MUST_EXIST);
        $quiz     = $DB->get_record('quiz', ['id' => $cm->instance], '*', MUST_EXIST);
        $category = $DB->get_record('question_categories', ['id' => $categoryid], '*', MUST_EXIST);

        $context = \context_module::instance($cmid);
        self::validate_context($context);
        require_capability('mod/quiz:manage', $context);

        // ── 3. Execute based on mode ────────────────────────────────
        $added = 0;

        if ($mode === 'all') {
            // Get all question bank entries in the category.
            $entries = $DB->get_records('question_bank_entries', [
                'questioncategoryid' => $categoryid,
            ]);

            foreach ($entries as $entry) {
                // Get the latest version of each question.
                $version = $DB->get_record_sql(
                    "SELECT qv.questionid
                       FROM {question_versions} qv
                      WHERE qv.questionbankentryid = :entryid
                        AND qv.status = 'ready'
                   ORDER BY qv.version DESC
                      LIMIT 1",
                    ['entryid' => $entry->id]
                );

                if (!$version) {
                    // Try without status filter as fallback.
                    $version = $DB->get_record_sql(
                        "SELECT qv.questionid
                           FROM {question_versions} qv
                          WHERE qv.questionbankentryid = :entryid
                       ORDER BY qv.version DESC
                          LIMIT 1",
                        ['entryid' => $entry->id]
                    );
                }

                if ($version) {
                    quiz_add_quiz_question($version->questionid, $quiz);
                    $added++;
                }
            }

            $message = "Added {$added} question(s) from category '{$category->name}' to quiz '{$quiz->name}'.";

        } else {
            // Random mode: add N random question references.
            // Clamp numquestions to available count.
            $available = (int) $DB->count_records('question_bank_entries', [
                'questioncategoryid' => $categoryid,
            ]);

            if ($numquestions > $available && !$includesubcategories) {
                $numquestions = $available;
            }

            if ($numquestions <= 0) {
                return [
                    'success'         => false,
                    'quiz_name'       => $quiz->name,
                    'mode'            => $mode,
                    'questions_added' => 0,
                    'message'         => "No questions available in category '{$category->name}'.",
                ];
            }

            // Use Moodle 5.x structure class for random questions.
            // quiz_add_random_questions() is deprecated since Moodle 4.3 (MDL-72321).
            try {
                $quizobj = \mod_quiz\quiz_settings::create($quiz->id);
                $structure = $quizobj->get_structure();

                // Build filter condition in the format Moodle expects:
                // $filtercondition['filter']['category']['values'][0] = categoryid
                $filtercondition = [
                    'filter' => [
                        'category' => [
                            'values' => [$categoryid],
                            'filteroptions' => [
                                'includesubcategories' => $includesubcategories,
                            ],
                        ],
                    ],
                ];

                $structure->add_random_questions(
                    0,                  // page
                    $numquestions,       // number of random questions
                    $filtercondition
                );
                $added = $numquestions;
            } catch (\Exception $e) {
                return [
                    'success'         => false,
                    'quiz_name'       => $quiz->name,
                    'mode'            => $mode,
                    'questions_added' => 0,
                    'message'         => "Failed to add random questions: " . $e->getMessage(),
                ];
            }

            $message = "Added {$added} random question reference(s) from category '{$category->name}' to quiz '{$quiz->name}'.";
        }

        // ── 4. Purge caches ─────────────────────────────────────────
        \course_modinfo::purge_course_cache($courseid);
        // Rebuild quiz grade using Moodle 5.x API (quiz_update_sumgrades deprecated since 4.2).
        $quizobj = \mod_quiz\quiz_settings::create($quiz->id);
        $quizobj->get_grade_calculator()->recompute_quiz_sumgrades();

        return [
            'success'         => true,
            'quiz_name'       => $quiz->name,
            'mode'            => $mode,
            'questions_added' => $added,
            'message'         => $message,
        ];
    }

    /**
     * Describe return values.
     */
    public static function execute_returns(): external_single_structure {
        return new external_single_structure([
            'success'         => new external_value(PARAM_BOOL, 'True on success'),
            'quiz_name'       => new external_value(PARAM_TEXT, 'Name of the quiz'),
            'mode'            => new external_value(PARAM_ALPHA, 'Mode used: all or random'),
            'questions_added' => new external_value(PARAM_INT,  'Number of questions/references added'),
            'message'         => new external_value(PARAM_TEXT, 'Result message'),
        ]);
    }
}
