<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>BIA MFA Capstone</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 700px;
            margin: 50px auto;
            padding: 20px;
            background: #f4f6f8;
            color: #222;
        }
        main {
            background: white;
            padding: 28px;
            border-radius: 12px;
        }
        input, button {
            padding: 10px;
            margin: 8px 0;
        }
        input { width: 90%; }
        button { cursor: pointer; }
        .message { color: #a22; }
    </style>
</head>
<body>
    <main>
        <h1>BIA Multi-Factor Authentication</h1>
        {% for message in get_flashed_messages() %}
            <p class="message">{{ message }}</p>
        {% endfor %}
        {% block content %}{% endblock %}
    </main>
</body>
</html>
