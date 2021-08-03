import json

json_settings = json.dumps([
    
    {
        "type": "bool",
        "title": "Connection",
        "desc": "Turn the connection on or off",
        "section": "General",
        "key": "connection"
    },
    {
        "type": "string",
        "title": "IP",
        "desc": "GQRX remote control IP",
        "section": "General",
        "key": "ip"
    },
    {
        "type": "string",
        "title": "Port",
        "desc": "GQRX remote control port",
        "section": "General",
        "key": "port"
    },
    {
        "type": "string",
        "title": "Update Delay",
        "desc": "Delay in seconds between data updates",
        "section": "General",
        "key": "update"
    }
])
