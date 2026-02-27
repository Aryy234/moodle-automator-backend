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
];

// Pre-built service so the function automatically appears in the Moodle
// "External services" list. The admin can also add the function to any
// custom service manually.
$services = [
    'Section Edit Service' => [
        'functions'       => ['local_sectionedit_update_section_summary'],
        'restrictedusers' => 0,
        'enabled'         => 1,
        'shortname'       => 'local_sectionedit',
    ],
];
