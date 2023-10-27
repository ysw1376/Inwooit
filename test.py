from flask import Flask, request, render_template_string

app = Flask(__name__)

# HTML 템플릿
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>바이트 변환 테스트</title>
</head>
<body>
    <h1>변환할 파일을 업로드 하세요</h1>
    <form method="post" enctype="multipart/form-data">
        <textarea name="text" rows="10" cols="40">{{ text }}</textarea><br>
        <input type="submit" name="action" value="텍스트로 자르기">
        <input type="file" name="file">
        <input type="submit" name="action" value="파일로 자르기">
    </form>
    <h2>자른 텍스트:</h2>
    <p>{{ chopped_text }}</p>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    text = ''
    chopped_text = ''

    if request.method == 'POST':
        action = request.form['action']
        
        if action == '텍스트로 변환':
            text = request.form['text']
            # 여기에서 텍스트를 원하는 길이(예: 255바이트)로 자를 수 있습니다.
            chopped_text = text[:255]
        elif action == '파일로 변환':
            uploaded_file = request.files['file']
            if uploaded_file:
                file_data = uploaded_file.read(255)  # 처음 255바이트를 읽음
                chopped_text = file_data.decode('utf-8', errors='ignore')  # 바이트를 문자열로 변환

    return render_template_string(html_template, text=text, chopped_text=chopped_text)

if __name__ == '__main__':
    app.run()