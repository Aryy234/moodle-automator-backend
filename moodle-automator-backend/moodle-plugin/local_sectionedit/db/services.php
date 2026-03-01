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
];

// Pre-built service so the functions automatically appear in the Moodle
// "External services" list. The admin can also add the functions to any
// custom service manually.
$services = [
    'Section Edit Service' => [
        'functions'       => [
            'local_sectionedit_update_section_summary',
            'local_sectionedit_add_label_to_section',
        ],
        'restrictedusers' => 0,
        'enabled'         => 1,
        'shortname'       => 'local_sectionedit',
    ],
];
