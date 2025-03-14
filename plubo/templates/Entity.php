<?php

namespace PluginPlaceholder\Entities;

class EntityName
{

    const table_name = '';

    public $id;


    public function __construct($id = null)
    {
        if ($id) {
            $this->id = $id;
            $this->init();
        }
    }

    private function init()
    {
        global $wpdb;
        $table = $wpdb->prefix . self::table_name;

        $results = $wpdb->get_row(
            $wpdb->prepare(
                "
                SELECT * FROM $table WHERE id = %d
                ",
                $this->id
            ),
            ARRAY_A
        );

        if ($results) {
            foreach ($results as $key => $value) {
                $this->{$key} = $value;
            }
        }
    }

    public function set_field($field_name, $value)
    {
        global $wpdb;
        $wpdb->update(
            $wpdb->prefix . self::table_name,
            [$field_name => $value],
            ['id' => $this->id]
        );
        $this->{$field_name} = $value;

        return $this;
    }

    public function create($args)
    {
        global $wpdb;

        foreach ($args as $key => $value) {
            $this->{$key} = $value;
        }

        $wpdb->insert($wpdb->prefix . self::table_name, $args);
        $this->id = $wpdb->insert_id;

        return $this->id;
    }

    public function delete()
    {
        global $wpdb;

        $wpdb->delete(
            $wpdb->prefix . self::table_name,
            ['id' => $this->id],
            ['%d']
        );

        return true;
    }
}
