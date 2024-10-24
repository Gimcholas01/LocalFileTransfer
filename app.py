from flask import *
from werkzeug.utils import secure_filename
import os
import qrcode
import subprocess

def get_local_ip():
    # Define the PowerShell command
    powershell_command = '''
    Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -ne $null } | ForEach-Object { $_.IPv4Address.IPAddress }
    '''
    
    # Run the PowerShell command and capture the output
    result = subprocess.run(["powershell", "-Command", powershell_command], capture_output=True, text=True)
    
    if result.returncode == 0:
        # Return the output (strip any extra whitespace)
        return result.stdout.strip()
    else:
        # Return an error message if the command failed
        return f"Error: {result.stderr.strip()}"

app = Flask(__name__)

# Define the folder to save uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return redirect(url_for('upload'))

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/download')
def download():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('download.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part in the request'})

    files = request.files.getlist('file')

    if not files:
        return jsonify({'status': 'error', 'message': 'No selected file'})

    for file in files:
        if file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
    
    return redirect(url_for('upload'))


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    # create qr
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data("http://" + get_local_ip()+":8000")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save("ScanMe_FileTransfer.png")
    
    # display qr
    os.startfile("ScanMe_FileTransfer.png")
    
    # start server
    app.run(host='0.0.0.0', port=8000, debug=False)