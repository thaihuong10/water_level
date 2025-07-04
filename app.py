from flask import Flask, render_template, request, redirect, url_for
import os
from utils import read_excel_openpyxl, get_daily_extremes
from datetime import datetime
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            return "Vui lòng chọn file hợp lệ."

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            data = read_excel_openpyxl(filepath)
            available_dates = sorted(list(set(d["timestamp"].date() for d in data)))
            if not available_dates:
                return "Không tìm thấy dữ liệu ngày hợp lệ trong file."

            default_date = available_dates[0].strftime("%Y-%m-%d")
            return redirect(url_for('result', filename=filename, date=default_date))
        except Exception as e:
            return f"Lỗi xử lý file: {str(e)}"

    return render_template('index.html')


@app.route('/result', methods=['GET', 'POST'])
def result():
    if request.method == 'POST':
        filename = request.form.get('filename')
        selected_date = request.form.get('date')
        return redirect(url_for('result', filename=filename, date=selected_date))

    filename = request.args.get('filename')
    date_str = request.args.get('date')

    if not filename or not date_str:
        return redirect(url_for('index'))

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return "Không tìm thấy file đã upload."

    try:
        data = read_excel_openpyxl(filepath)
        available_dates = sorted(list(set(d["timestamp"].date() for d in data)))
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        max_list, min_list = get_daily_extremes(data, date_str)
        selected_data = [d for d in data if d["timestamp"].date() == selected_date]
        selected_data.sort(key=lambda x: x["timestamp"])

        labels = [d["timestamp"].strftime("%H:%M") for d in selected_data]
        values = [d["water_level"] for d in selected_data]
        peak_times = [d["timestamp"].strftime("%H:%M") for d in max_list]
        trough_times = [d["timestamp"].strftime("%H:%M") for d in min_list]

        return render_template(
            'result.html',
            date=date_str,
            filename=filename,
            labels=labels,
            values=values,
            peak_times=peak_times,
            trough_times=trough_times,
            peak_value=max_list[0]["water_level"] if max_list else None,
            trough_value=min_list[0]["water_level"] if min_list else None,
            available_dates=[d.strftime("%Y-%m-%d") for d in available_dates]
        )
    except Exception as e:
        return f"Lỗi khi xử lý kết quả: {str(e)}"


if __name__ == '__main__':
    app.run(debug=True)
