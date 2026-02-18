<?php

namespace PluginPlaceholder\Functionality;

class Crons
{

    protected $plugin_name;
    protected $plugin_version;

    public function __construct($plugin_name, $plugin_version)
    {
        $this->plugin_name = $plugin_name;
        $this->plugin_version = $plugin_version;
        $cron_hook = "{$this->plugin_name}_cron_hook";

        add_action('init', [$this, 'register_crons']);
        add_action($cron_hook, [$this, 'example_cron_callback']);
    }

    public function register_crons()
    {
        $cron_hook = "{$this->plugin_name}_cron_hook";

        // Prefer Action Scheduler when it is available.
        if (function_exists('as_schedule_recurring_action') && function_exists('as_has_scheduled_action')) {
            if (!\as_has_scheduled_action($cron_hook)) {
                \as_schedule_recurring_action(time(), HOUR_IN_SECONDS, $cron_hook, [], $this->plugin_name);
            }
            return;
        }

        // Fallback to WP-Cron.
        if (!wp_next_scheduled($cron_hook)) {
            wp_schedule_event(time(), 'hourly', $cron_hook);
        }
    }

    public function example_cron_callback()
    {
        // CRON CALLBACK CODE
    }
}
