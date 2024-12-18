import os
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QComboBox, QProgressBar, QGroupBox, QHBoxLayout
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
import yt_dlp


class VideoDownloader(QWidget):
    def __init__(self):
        super().__init__()

        # Set default download folder to the user's Downloads directory
        self.default_download_folder = os.path.join(os.path.expanduser("~"), "Downloads")

        # Window Title and Size
        self.setWindowTitle("Modern Video Downloader")
        self.setGeometry(100, 100, 700, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QLabel {
                font-size: 16px;
                margin-bottom: 5px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                padding: 10px;
                border-radius: 5px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 14px;
            }
            QProgressBar {
                text-align: center;
                color: black;
                border: 1px solid #0078d7;
                border-radius: 5px;
            }
            QGroupBox {
                margin-top: 10px;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)

        # Main Layout
        self.layout = QVBoxLayout()

        # URL Input Section
        self.url_group = QGroupBox("Step 1: Enter Video URL")
        self.url_layout = QVBoxLayout()

        self.url_label = QLabel("Paste the video URL:")
        self.url_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.url_layout.addWidget(self.url_label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("e.g., https://www.youtube.com/watch?v=...")
        self.url_input.textChanged.connect(self.reset_on_new_link)
        self.url_layout.addWidget(self.url_input)

        self.fetch_formats_button = QPushButton("Fetch Video Info")
        self.fetch_formats_button.clicked.connect(self.fetch_formats)
        self.url_layout.addWidget(self.fetch_formats_button)

        self.url_group.setLayout(self.url_layout)
        self.layout.addWidget(self.url_group)

        # Video Preview Section
        self.preview_group = QGroupBox("Video Preview")
        self.preview_layout = QHBoxLayout()

        self.video_thumbnail = QLabel()
        self.video_thumbnail.setPixmap(QPixmap())
        self.video_thumbnail.setFixedSize(200, 150)
        self.video_thumbnail.setScaledContents(True)
        self.preview_layout.addWidget(self.video_thumbnail)

        self.video_title = QLabel("Title: N/A")
        self.video_title.setWordWrap(True)
        self.preview_layout.addWidget(self.video_title)

        self.preview_group.setLayout(self.preview_layout)
        self.layout.addWidget(self.preview_group)

        # Quality Selection Section
        self.quality_group = QGroupBox("Step 2: Select Video Quality")
        self.quality_layout = QVBoxLayout()

        self.quality_selector = QComboBox()
        self.quality_selector.setEnabled(False)
        self.quality_layout.addWidget(self.quality_selector)

        self.quality_group.setLayout(self.quality_layout)
        self.layout.addWidget(self.quality_group)

        # File Rename Section
        self.rename_group = QGroupBox("Step 3: Rename Downloaded File (Optional)")
        self.rename_layout = QVBoxLayout()

        self.rename_label = QLabel("Enter the new file name (leave blank for default):")
        self.rename_layout.addWidget(self.rename_label)

        self.rename_input = QLineEdit()
        self.rename_input.setPlaceholderText("e.g., MyAwesomeVideo")
        self.rename_layout.addWidget(self.rename_input)

        self.rename_group.setLayout(self.rename_layout)
        self.layout.addWidget(self.rename_group)

        # Save Location Section
        self.save_group = QGroupBox("Step 4: Choose Save Location")
        self.save_layout = QVBoxLayout()

        self.save_button = QPushButton("Select Save Folder")
        self.save_button.clicked.connect(self.select_folder)
        self.save_layout.addWidget(self.save_button)

        # Prepopulate with the default Downloads folder
        self.selected_folder = QLabel(f"Default: {self.default_download_folder}")
        self.selected_folder.setStyleSheet("color: black; font-size: 14px;")
        self.save_layout.addWidget(self.selected_folder)

        self.save_group.setLayout(self.save_layout)
        self.layout.addWidget(self.save_group)

        # Download Button
        self.download_button = QPushButton("Download Video")
        self.download_button.clicked.connect(self.download_video)
        self.download_button.setEnabled(False)
        self.layout.addWidget(self.download_button)

        # Progress and Status Section
        self.progress_group = QGroupBox("Download Progress")
        self.progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; color: #333;")
        self.progress_layout.addWidget(self.status_label)

        self.progress_group.setLayout(self.progress_layout)
        self.layout.addWidget(self.progress_group)

        # Set Main Layout
        self.setLayout(self.layout)

    def reset_on_new_link(self):
        """Resets quality dropdown, video preview, and disables download button."""
        self.quality_selector.clear()
        self.quality_selector.setEnabled(False)
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.video_thumbnail.setPixmap(QPixmap())
        self.video_title.setText("Title: N/A")
        self.rename_input.clear()  # Clear rename input field
        self.rename_input.setPlaceholderText("")  # Reset placeholder text
        self.status_label.setText("Status: Ready for new video")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.selected_folder.setText(folder)
            self.selected_folder.setStyleSheet("color: black;")
        else:
            self.selected_folder.setText(f"Default: {self.default_download_folder}")
            self.selected_folder.setStyleSheet("color: black;")

    def fetch_formats(self):
        self.progress_bar.setValue(0)
        self.status_label.setText("Fetching video information...")

        url = self.url_input.text()

        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a video URL.")
            return

        try:
            self.quality_selector.clear()
            with yt_dlp.YoutubeDL() as ydl:
                info = ydl.extract_info(url, download=False)
                self.video_title.setText(f"Title: {info['title']}")

                # Fetch and display thumbnail
                thumbnail_url = info.get('thumbnail')
                if thumbnail_url:
                    pixmap = self.fetch_thumbnail(thumbnail_url)
                    self.video_thumbnail.setPixmap(pixmap)

                formats = info.get('formats', [])
                self.format_options = []

                # Extract all unique video formats
                seen_resolutions = set()
                for fmt in formats:
                    if fmt.get('vcodec') != 'none':  # Include video formats only
                        resolution = fmt.get('format_note', 'unknown')
                        ext = fmt.get('ext', 'unknown')
                        format_id = fmt.get('format_id')

                        # Avoid duplicates
                        if resolution not in seen_resolutions:
                            seen_resolutions.add(resolution)
                            self.format_options.append((f"{resolution} - {ext}", format_id))

                if not self.format_options:
                    QMessageBox.warning(self, "Error", "No video formats available for this video.")
                    return

                # Add options to the dropdown
                for display_text, _ in self.format_options:
                    self.quality_selector.addItem(display_text)

                self.quality_selector.setEnabled(True)
                self.download_button.setEnabled(True)
                self.status_label.setText("Video information fetched successfully!")

        except Exception as e:
            self.status_label.setText("Failed to fetch video information.")
            QMessageBox.critical(self, "Error", f"Failed to fetch video information: {str(e)}")

    def fetch_thumbnail(self, url):
        """Fetches the thumbnail image from a URL."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            return pixmap
        except Exception:
            return QPixmap()

    def download_video(self):
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting download...")

        url = self.url_input.text()
        selected_format = self.quality_selector.currentIndex()

        # Default to Downloads folder if none is selected
        save_path = self.selected_folder.text()
        if save_path.startswith("Default:"):
            save_path = self.default_download_folder

        # Get custom file name
        custom_name = self.rename_input.text()
        if not custom_name:
            custom_name = '%(title)s'

        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a video URL.")
            return

        if selected_format == -1:
            QMessageBox.warning(self, "Input Error", "Please select a video quality.")
            return

        try:
            format_id = self.format_options[selected_format][1]
            self.download_from_url(url, save_path, format_id, custom_name)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to download video: {str(e)}")

    def download_from_url(self, url, save_path, format_id, custom_name):
        def progress_hook(d):
            if d['status'] == 'downloading':
                downloaded_bytes = d.get('downloaded_bytes', 0)
                total_bytes = d.get('total_bytes', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)

                if total_bytes:
                    progress = int(downloaded_bytes / total_bytes * 100)
                    self.progress_bar.setValue(progress)

                self.status_label.setText(
                    f"Downloading... {progress}% - Speed: {self.format_size(speed)}/s - ETA: {self.format_time(eta)}"
                )
            elif d['status'] == 'finished':
                self.progress_bar.setValue(100)
                QMessageBox.information(self, "Success", "Download completed successfully!")
                self.progress_bar.setValue(0)  # Reset progress bar after success
                self.status_label.setText("Status: Idle")

        ydl_opts = {
            'outtmpl': os.path.join(save_path, f"{custom_name}.%(ext)s"),
            'format': format_id,
            'merge_output_format': 'mp4',
            'progress_hooks': [progress_hook],
        }

        self.progress_bar.setValue(0)
        self.status_label.setText("Starting download...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    @staticmethod
    def format_size(bytes_size):
        if bytes_size is None:
            return "Unknown size"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.2f} TB"

    @staticmethod
    def format_time(seconds):
        if seconds is None:
            return "Unknown"
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes):02}:{int(seconds):02}"


if __name__ == "__main__":
    app = QApplication([])
    window = VideoDownloader()
    window.show()
    app.exec_()
