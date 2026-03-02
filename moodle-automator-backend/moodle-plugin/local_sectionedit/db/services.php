<?php
// This file is part of Moodle - http://moodle.org/
//
// @package    local_sectionedit
// @copyright  2025 Moodle Automator
// @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later

defined('MOODLE_INTERNAL') || die();

$functions = [
    'local_sectionedit_update_section_summary' => [
        'classname'   => 'local_sectionedit\external\update_section_summary',
        'description'  => 'Update the summary (HTML content) of a course section.',
        'type'         => 'write',
        'ajax'         => true,
        'capabilities' => 'moodle/course:update',
    ],
    'local_sectionedit_add_label_to_section' => [
        'classname'   => 'local_sectionedit\external\add_label_to_section',
        'description'  => 'Create a new label (Text and media area) module inside a course section.',
        'type'         => 'write',
        'ajax'         => true,
        'capabilities' => 'moodle/course:manageactivities',
    ],
    'local_sectionedit_get_question_categories' => [
        'classname'    => 'local_sectionedit\external\get_question_categories',
        'description'  => 'Get question categories for a course from the question bank.',
        'type'         => 'read',
        'ajax'         => true,
        'capabilities' => 'moodle/question:viewall',
    ],
    'local_sectionedit_create_question_category' => [
        'classname'    => 'local_sectionedit\external\create_question_category',
        'description'  => 'Create a new question category in the question bank of a course.',
        'type'         => 'write',
        'ajax'         => true,
        'capabilities' => 'moodle/question:managecategory',
    ],
    'local_sectionedit_import_questions' => [
        'classname'    => 'local_sectionedit\external\import_questions',
        'description'  => 'Import questions from a file (Aiken/XML) into the question bank.',
        'type'         => 'write',
        'ajax'         => true,
        'capabilities' => 'moodle/question:add',
    ],
    'local_sectionedit_configure_quiz_questions' => [
        'classname'    => 'local_sectionedit\external\configure_quiz_questions',
        'description'  => 'Add questions from a category to a quiz (all or random).',
        'type'         => 'write',
        'ajax'         => true,
        'capabilities' => 'mod/quiz:manage',
    ],
    'local_sectionedit_update_quiz_settings' => [
        'classname'    => 'local_sectionedit\external\update_quiz_settings',
        'description'  => 'Update quiz settings such as time limit.',
        'type'         => 'write',
        'ajax'         => true,
        'capabilities' => 'mod/quiz:manage',
    ],
];

// Pre-built service so the functions automatically appear in the Moodle
// "External services" list. The admin can also add the functions to any
// custom service manually.
$services = [
    'Section Edit Service' => [
        'functions'       => [
            'local_sectionedit_update_section_summary',
            'local_sectionedit_add_label_to_section',
            'local_sectionedit_get_question_categories',
            'local_sectionedit_create_question_category',
            'local_sectionedit_import_questions',
            'local_sectionedit_configure_quiz_questions',
            'local_sectionedit_update_quiz_settings',
        ],
        'restrictedusers' => 0,
        'enabled'         => 1,
        'shortname'       => 'local_sectionedit',
    ],
];
