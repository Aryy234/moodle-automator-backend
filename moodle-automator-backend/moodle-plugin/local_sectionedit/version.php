<?php
// This file is part of Moodle - http://moodle.org/
//
// local_sectionedit – tiny plugin to edit section summaries via Web Service.
//
// @package    local_sectionedit
// @copyright  2025 Moodle Automator
// @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later

defined('MOODLE_INTERNAL') || die();

$plugin->component = 'local_sectionedit';
$plugin->version   = 2025061401;   // YYYYMMDDXX  — v1.1: add_label_to_section
$plugin->requires  = 2024100700;   // Moodle 4.5+
$plugin->maturity  = MATURITY_STABLE;
$plugin->release   = '1.1.0';
