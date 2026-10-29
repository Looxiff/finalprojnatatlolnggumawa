from datetime import datetime
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCalendarWidget, QTimeEdit, QSpinBox, QMessageBox,
    QStackedWidget, QWidget, QFrame
)
from PyQt6.QtGui import QTextCharFormat, QColor


class CustomCalendarWidget(QCalendarWidget):
    """Calendar that greys out and disables overbooked dates (5 reservations/day limit)."""
    def __init__(self, seat_manager, parent=None):
        super().__init__(parent)
        self.seat_manager = seat_manager
        self.setMinimumDate(QDate.currentDate())
        self.update_disabled_dates()

    def update_disabled_dates(self):
        disabled_fmt = QTextCharFormat()
        disabled_fmt.setBackground(QColor("#e0e0e0"))
        disabled_fmt.setForeground(QColor("#a0a0a0"))

        today = QDate.currentDate()
        for i in range(60):
            check_date = today.addDays(i)
            date_str = check_date.toString("yyyy-MM-dd")
            if self.seat_manager.is_date_overbooked(date_str):
                self.setDateTextFormat(check_date, disabled_fmt)


class SeatReservationDialog(QDialog):
    def __init__(self, seat_id, seat_manager, parent=None):
        super().__init__(parent)
        self.seat_id = seat_id
        self.seat_manager = seat_manager
        self.status = seat_manager.status(seat_id)
        self.student_number = ""

        self.setWindowTitle("Library Seat Access")
        self.setFixedWidth(380)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog { background: #fffdf5; }
            QLabel#title { color: #171717; font-size: 20px; font-weight: 700; }
            QLabel#sub { color: #5b5b5b; font-size: 12px; }
            QLabel#prompt { color: #333333; font-size: 12px; font-weight: 600; }
            
            /* Section Headers & Field Labels */
            QLabel { color: #171717; font-size: 13px; font-weight: 600; }

            /* Text & Input Controls */
            QLineEdit { 
                border: 1px solid #cfc8b4; 
                border-radius: 7px; 
                padding: 11px; 
                background: #ffffff; 
                color: #111111; 
                font-size: 14px; 
            }
            QLineEdit::placeholder { color: #888888; }

            /* --- TimeEdit & SpinBox --- */
            QTimeEdit, QSpinBox { 
                border: 1px solid #cfc8b4; 
                border-radius: 7px; 
                padding: 4px 6px; 
                background: #ffffff; 
                color: #111111; 
                font-size: 13px;
                min-width: 95px;
                min-height: 28px;
            }

            QTimeEdit::up-button, QSpinBox::up-button,
            QTimeEdit::down-button, QSpinBox::down-button {
                width: 16px;
            }

            QTimeEdit::up-button, QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 18px;
                border-left: 1px solid #e0d8c3;
                border-bottom: 1px solid #e0d8c3;
                border-top-right-radius: 6px;
                background: #faf8f0;
            }
            QTimeEdit::down-button, QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 18px;
                border-left: 1px solid #e0d8c3;
                border-bottom-right-radius: 6px;
                background: #faf8f0;
            }

            QTimeEdit::up-button:hover, QSpinBox::up-button:hover,
            QTimeEdit::down-button:hover, QSpinBox::down-button:hover {
                background: #ffec99;
            }

            /* --- Complete Calendar Light Theme Overhaul --- */
            QCalendarWidget {
                background-color: #ffffff;
                border: 1px solid #cfc8b4;
                border-radius: 8px;
            }
            
            /* Top Navigation Bar (Month/Year Header) */
            QCalendarWidget QWidget#qt_calendar_navigationbar { 
                background-color: #ffcc00; 
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
            }
            QCalendarWidget QToolButton {
                color: #111111;
                font-weight: bold;
                background-color: transparent;
                border: none;
                margin: 2px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #ffe066;
                border-radius: 4px;
            }
            QCalendarWidget QMenu {
                background-color: #ffffff;
                color: #111111;
            }

            /* Date Grid & Numbers */
            QCalendarWidget QAbstractItemView:enabled {
                color: #111111;
                background-color: #ffffff;
                selection-background-color: #ffcc00;
                selection-color: #111111;
                font-size: 12px;
            }
            
            /* Days Header (Sun, Mon, Tue...) */
            QCalendarWidget QWidget {
                alternate-background-color: #fbf8eb;
                color: #111111;
            }

            /* Buttons */
            QPushButton { 
                background: #ffcc00; 
                border: 1px solid #e4b700; 
                border-radius: 7px; 
                padding: 10px 14px; 
                font-weight: 700; 
                color: #111111; 
            }
            QPushButton#secondary, QPushButton#cancel { 
                background: #ffffff; 
                border: 1px solid #d7d0bd; 
                font-weight: 700; 
                color: #111111; 
            }
            QPushButton:hover {
                background: #ffe066;
            }
            QPushButton#secondary:hover, QPushButton#cancel:hover {
                background: #f7f4ea;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 22)
        layout.setSpacing(12)

        # Title & Subtitle Header
        title = QLabel("Library Seat Access")
        title.setObjectName("title")
        
        subtitle_text = f"Seat: {self.seat_id}  •  Status: {self.status.title()}"
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("sub")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color:#e3dcc9")
        layout.addWidget(divider)

        # Pages: Page 0 = Mandatory Login & Action, Page 1 = Calendar Scheduling
        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_login_page())
        self.pages.addWidget(self._build_schedule_page())
        layout.addWidget(self.pages)

    def _build_login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Dynamic login prompt based on current seat state
        if self.status == "occupied":
            prompt_text = "Enter your student number to update status or check out:"
        elif self.status == "reserved":
            prompt_text = "Enter your student number to check in or reserve a new slot:"
        else:
            prompt_text = "Enter your student number to proceed:"

        prompt = QLabel(prompt_text)
        prompt.setObjectName("prompt")
        layout.addWidget(prompt)

        # Student Number Login Input
        self.student_input = QLineEdit()
        self.student_input.setPlaceholderText("Enter Student Number")
        self.student_input.setClearButtonEnabled(True)
        layout.addWidget(self.student_input)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        # Two primary option choices per login prompt
        if self.status == "available":
            self.sched_btn = QPushButton("Reserve Date")
            self.sched_btn.setObjectName("secondary")
            self.sched_btn.clicked.connect(self._proceed_to_reserve)

            action_btn = QPushButton("Update Status")
            action_btn.clicked.connect(self._occupy_now)

            buttons.addWidget(self.sched_btn)
            buttons.addWidget(action_btn)
        else:
            cancel_btn = QPushButton("Release / Check Out")
            cancel_btn.setObjectName("secondary")
            cancel_btn.clicked.connect(self._logout)

            action_btn = QPushButton("Check In" if self.status == "reserved" else "Update Status")
            action_btn.clicked.connect(self._occupy_now if self.status == "reserved" else self._logout)

            buttons.addWidget(cancel_btn)
            buttons.addWidget(action_btn)

        layout.addLayout(buttons)
        self.student_input.setFocus()
        return page

    def _build_schedule_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header_lbl = QLabel("Select Reservation Date:")
        layout.addWidget(header_lbl)

        self.calendar = CustomCalendarWidget(self.seat_manager)
        layout.addWidget(self.calendar)

        time_layout = QHBoxLayout()
        time_layout.setSpacing(6)
        
        lbl_start = QLabel("Start Time:")
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("hh:mm AP")
        self.time_edit.setTime(QTime.currentTime())

        lbl_duration = QLabel("Duration (Hrs):")
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 4)

        time_layout.addWidget(lbl_start)
        time_layout.addWidget(self.time_edit)
        time_layout.addSpacing(8)
        time_layout.addWidget(lbl_duration)
        time_layout.addWidget(self.duration_spin)
        
        layout.addLayout(time_layout)

        btn_row = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.setObjectName("cancel")
        back_btn.clicked.connect(lambda: self.pages.setCurrentIndex(0))

        confirm_btn = QPushButton("Confirm Schedule")
        confirm_btn.clicked.connect(self._confirm_reservation)

        btn_row.addWidget(back_btn)
        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

        return page

    def _validate_student_login(self):
        """Forces student login validation before any downstream action is permitted."""
        student_no = self.student_input.text().strip()
        if not student_no:
            QMessageBox.warning(self, "Login Required", "Please enter your student number before proceeding.")
            return None
        self.student_number = student_no
        return student_no

    def _proceed_to_reserve(self):
        if self._validate_student_login():
            self.pages.setCurrentIndex(1)

    def _occupy_now(self):
        student_no = self._validate_student_login()
        if not student_no:
            return

        ok, msg = self.seat_manager.occupy(self.seat_id, student_no)
        if ok:
            QMessageBox.information(self, "Status Updated", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Seat Access", msg)

    def _logout(self):
        student_no = self._validate_student_login()
        if not student_no:
            return

        ok, msg = self.seat_manager.release(self.seat_id, student_no)
        if ok:
            QMessageBox.information(self, "Status Updated", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Seat Access", msg)

    def _confirm_reservation(self):
        selected_qdate = self.calendar.selectedDate()
        date_str = selected_qdate.toString("yyyy-MM-dd")

        if self.seat_manager.is_date_overbooked(date_str):
            QMessageBox.warning(self, "Overbooked", "This date has reached the maximum 5 reservations limit.")
            return

        selected_time = self.time_edit.time()
        start_dt = datetime(
            selected_qdate.year(), selected_qdate.month(), selected_qdate.day(),
            selected_time.hour(), selected_time.minute()
        )
        duration = self.duration_spin.value()

        ok, msg = self.seat_manager.reserve(
            self.seat_id, self.student_number, date_str, start_dt, duration
        )

        if ok:
            QMessageBox.information(self, "Reservation Successful", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Reservation Error", msg)