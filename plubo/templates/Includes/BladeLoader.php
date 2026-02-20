<?php

namespace PluginPlaceholder\Includes;

use eftec\bladeone\BladeOne;

class BladeLoader
{
    private static $instance;
    private $blade;

    private function __construct()
    {
        $views_path = plugin_dir_path(dirname(__FILE__)) . 'Views';
        $cache_path = plugin_dir_path(dirname(__FILE__)) . 'cache';

        if (!file_exists($cache_path)) {
            wp_mkdir_p($cache_path);
        }

        $this->blade = new BladeOne($views_path, $cache_path, BladeOne::MODE_AUTO);
    }

    public static function getInstance()
    {
        if (!self::$instance) {
            self::$instance = new self();
        }

        return self::$instance;
    }

    public function template($view, $data = [])
    {
        return $this->blade->run($view, $data);
    }
}
