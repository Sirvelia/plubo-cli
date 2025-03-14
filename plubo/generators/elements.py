import os
import curses
from pathlib import Path
from plubo.generators import project  # Import function to get the plugin name

def add_element(stdscr):
    """Displays a menu to select an entity type and prompts for details."""
    curses.curs_set(0)  # Hide cursor
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    
    stdscr.nodelay(0)
    stdscr.clear()
    stdscr.addstr(2, 2, "🔄 Add Entity")
    stdscr.refresh()
    
    options = ["Shortcode", "Route", "Endpoint", "Role", "Custom Product", "Custom Post Type", "Taxonomy"]
    current_row = 0
    
    while True:
        stdscr.clear()
        stdscr.addstr(2, 2, "🔄 Select an Entity Type:")
        
        for idx, option in enumerate(options):
            x = 4
            y = 4 + idx
            if idx == current_row:
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(y, x, option)
                stdscr.attroff(curses.color_pair(3))
            else:
                stdscr.addstr(y, x, option)
        
        stdscr.refresh()
        key = stdscr.getch()
        
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            selection = options[current_row]
            if selection == "Endpoint":
                configure_endpoint(stdscr)
            break
        
    curses.curs_set(0)  # Hide cursor

def configure_endpoint(stdscr):
    """Prompts the user to configure an endpoint."""
    stdscr.clear()
    stdscr.addstr(2, 2, "Configure Endpoint")
    stdscr.refresh()
    
    type_options = ["GetEndpoint", "PostEndpoint", "PutEndpoint", "DeleteEndpoint"]
    type_index = 0
    
    while True:
        stdscr.clear()
        stdscr.addstr(4, 2, "Select Type:")
        
        for idx, option in enumerate(type_options):
            y = 6 + idx
            if idx == type_index:
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(y, 4, option)
                stdscr.attroff(curses.color_pair(3))
            else:
                stdscr.addstr(y, 4, option)
        
        stdscr.refresh()
        key = stdscr.getch()
        
        if key == curses.KEY_UP and type_index > 0:
            type_index -= 1
        elif key == curses.KEY_DOWN and type_index < len(type_options) - 1:
            type_index += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            type_choice = type_options[type_index]
            break
    
    curses.curs_set(1)
    
    stdscr.addstr(12, 2, "Namespace (default: " + project.detect_plugin_name() + "/v1):")
    curses.echo()
    stdscr.move(14, 2)
    namespace = stdscr.getstr().decode("utf-8").strip()
    if not namespace:
        namespace = project.detect_plugin_name() + "/v1"
    
    stdscr.addstr(16, 2, "Path (example: test):")
    stdscr.move(18, 2)
    path = stdscr.getstr().decode("utf-8").strip()
    curses.noecho()
    
    create_api_endpoint_file(namespace, path, type_choice)
    
    stdscr.clear()
    stdscr.addstr(2, 2, f"✅ Endpoint '{namespace}/{path}' ({type_choice}) created.")
    stdscr.addstr(6, 2, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def create_api_endpoint_file(namespace, path, type_choice):
    """Creates or updates the ApiEndpoints.php file with a new endpoint inside add_endpoints function."""
    plugin_root = Path(os.getcwd())
    functionality_dir = plugin_root / "Functionality"
    api_file = functionality_dir / "ApiEndpoints.php"
    template_file = Path(__file__).parent.parent / "templates/Functionality.php"
    
    functionality_dir.mkdir(parents=True, exist_ok=True)
    
    if not api_file.exists():
        api_file.write_text(template_file.read_text())
    
    with api_file.open("r", encoding="utf-8") as f:
        content = f.read()
    
    endpoint_code = f"""
        $endpoints[] = new {type_choice}(
            '{namespace}',
            '{path}',
            [$this, ''],
            function() {{
                return current_user_can('edit_posts');
            }}
        );
    """
    
    # Find the start of the add_endpoints function
    function_start = content.find("public function add_endpoints")
    if function_start == -1:
        # If the function doesn't exist, create it
        insert_position = content.rfind("}")
        content = content[:insert_position] + f"""
    public function add_endpoints($endpoints) {{
        {endpoint_code.strip()}
        return $endpoints;
    }}
}}""" + content[insert_position+1:]
    else:
        # Find the return statement inside the add_endpoints function
        return_start = content.find("return $endpoints;", function_start)
        if return_start == -1:
            # If there's no return statement, append the endpoint code before the closing brace
            closing_brace = content.rfind("}", function_start)
            content = content[:closing_brace] + endpoint_code + "\n    " + content[closing_brace:]
        else:
            # Insert the endpoint code before the return statement
            content = content[:return_start] + endpoint_code + "\n    " + content[return_start:]
    
    with api_file.open("w", encoding="utf-8") as f:
        f.write(content)
