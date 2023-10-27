import base64

# Flask와 관련된 라이브러리 임포트
from flask import Flask, request, render_template_string

app = Flask(__name__)

# HTML 템플릿
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Base64 변환 및 자르기</title>
</head>
<body>
    <h1>Base64인코딩 방식 >> 파일이나</h1>
    <form method="post" enctype="multipart/form-data">
        <textarea name="text" rows="10" cols="40">{{ text }}</textarea><br>
        <input type="submit" name="action" value="텍스트 변환">
        <input type="file" name="file">
        <input type="submit" name="action" value="파일 변환">
    </form>
    <h2>변환 결과:</h2>
    <p>{{ converted_text }}</p>
</body>
</html>
"""

def text_to_base64(text):
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')

@app.route('/', methods=['GET', 'POST'])
def index():
    text = ''
    converted_text = ''

    if request.method == 'POST':
        action = request.form['action']
        
        if action == '텍스트 변환':
            text = request.form['text']
            # 텍스트를 Base64로 변환
            converted_text = text_to_base64(text)
            # Base64로 인코딩된 데이터를 255바이트로 자르기
            converted_text = converted_text[:255]
        elif action == '파일 변환':
            uploaded_file = request.files['file']
            if uploaded_file:
                file_data = uploaded_file.read()
                # 파일을 Base64로 변환
                converted_text = base64.b64encode(file_data).decode('utf-8')
                # Base64로 인코딩된 데이터를 255바이트로 자르기
                converted_text = converted_text[:255]

    return render_template_string(html_template, text=text, converted_text=converted_text)

if __name__ == '__main__':
    app.run()