<?php
// This file is part of Moodle - http://moodle.org/
//
// @package    local_sectionedit
// @copyright  2025 Moodle Automator
// @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later

defined('MOODLE_INTERNAL') || die();

$capabilities = [
    'local/sectionedit:updatesummary' => [
        'captype'      => 'write',
        'contextlevel' => CONTEXT_COURSE,
        'archetypes'   => [
            'editingteacher' => CAP_ALLOW,
            'manager'        => CAP_ALLOW,
        ],
    ],
];
