from flask import *
from werkzeug.utils import secure_filename
import os
import qrcode
import subprocess
import logging


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

# Define the folder to save files for conversion
CONVERT_FOLDER = 'convert'
app.config['CONVERT_FOLDER'] = CONVERT_FOLDER

# Ensure the upload folder exists
if not os.path.exists(CONVERT_FOLDER):
    os.makedirs(CONVERT_FOLDER)


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

@app.route('/convert')
def convert():
    file = "" 
    return render_template('convert.html', file=file)

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


@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part in the request'})

    file = request.files["file"]

    if not file:
        return jsonify({'status': 'error', 'message': 'No selected file'})

    format = request.form.get("file_type").lower()

    if file.filename != '':
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['CONVERT_FOLDER'], filename)
        file.save(filepath)

        output_name = ''.join(e for e in file.filename.split(".")[0]  if e.isalnum()) + "." + format
        output_filepath = os.path.join(app.config['CONVERT_FOLDER'], output_name)
        command = f"ffmpeg -i {filepath} {output_filepath}" 
        os.system(command) 
        
        os.system(f"del {filepath}") 

        return render_template("convert.html", file=output_name)


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route("/convert/<filename>")
def download_convert(filename):
    return send_from_directory(app.config['CONVERT_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.debug = True
    ## create qr
    #qr = qrcode.QRCode(version=1, box_size=10, border=5)
    #qr.add_data("http://" + get_local_ip()+":8000")
    #qr.make(fit=True)
    #img = qr.make_image(fill_color="black", back_color="white")
    #img.save("ScanMe_FileTransfer.png")
    
    ## display qr
    #os.startfile("ScanMe_FileTransfer.png")
    
    # start server
    app.run(host='0.0.0.0', port=8000, debug=False)
