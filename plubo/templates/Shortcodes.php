<?php

namespace PluginPlaceholder\Functionality;

class Shortcodes
{

    protected $plugin_name;
    protected $plugin_version;

    public function __construct($plugin_name, $plugin_version)
    {
        $this->plugin_name = $plugin_name;
        $this->plugin_version = $plugin_version;

        add_action('init', [$this, 'add_shortcodes']);
        add_action('wp_enqueue_scripts', [$this, 'register_scripts']);
    }

    public function register_scripts()
    {
        // wp_register_style('test', PLUGIN_PLACEHOLDER_URL . pb_asset('app.css'), [], $this->plugin_version);
        // wp_register_script('test', PLUGIN_PLACEHOLDER_URL . pb_asset('app.js'), [], $this->plugin_version);
    }

    public function add_shortcodes()
    {
        //add_shortcode( 'test', [$this, 'test_shortcode'] );
    }

    public function test_shortcode($atts, $content = "")
    {
        // wp_enqueue_style('test');
        // wp_enqueue_script('test');

        // ob_start();
        // include PLUGIN_PLACEHOLDER_PATH . 'Views/test.php';
        // return ob_get_clean();
    }
}
