STYLE = """
    QWidget {
        background-color: #2c3e50;
        color: #ecf0f1;
        font-family: 'Segoe UI', sans-serif;
    }
    QListWidget {
        background-color: #243342;
        border: none;
        border-radius: 6px;
        padding: 4px;
        outline: none;
    }
    QListWidget::item {
        padding: 2px 0px;
        border-radius: 4px;
        color: #bdc3c7;
        font-size: 13px;
    }
    QListWidget::item:hover {
        background-color: #2e4057;
        color: #ecf0f1;
    }
    QListWidget::item:selected {
        background-color: #3498db;
        color: white;
    }

    /* ── New channel button ───────────────────────────────── */
    QPushButton#newChannelBtn {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton#newChannelBtn:hover   { background-color: #2980b9; }
    QPushButton#newChannelBtn:pressed { background-color: #2471a3; }
    QPushButton#newChannelBtn:disabled {
        background-color: #4a6278;
        color: #bdc3c7;
    }

    /* ── ⓘ Info button ───────────────────────────────────── */
    QPushButton#infoBtn {
        background-color: transparent;
        color: #7fb3d3;
        border: 2px solid #7fb3d3;
        border-radius: 13px;          /* circle: half of fixed size 26px */
        font-size: 12px;
        font-weight: bold;
        padding: 0px;
    }
    QPushButton#infoBtn:hover {
        background-color: #2e4057;
        color: #aed6f1;
        border-color: #aed6f1;
    }
    QPushButton#infoBtn:pressed {
        background-color: #3498db;
        color: white;
        border-color: #3498db;
    }

    /* ── Join button (green) ─────────────────────────────── */
    QPushButton#joinBtn {
        background-color: #27ae60;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        padding: 0px;
    }
    QPushButton#joinBtn:hover   { background-color: #229954; }
    QPushButton#joinBtn:pressed { background-color: #1e8449; }
    QPushButton#joinBtn:disabled {
        background-color: #4a6278;
        color: #bdc3c7;
    }

    /* ── Leave button (red) ──────────────────────────────── */
    QPushButton#leaveBtn {
        background-color: #e74c3c;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        padding: 0px;
    }
    QPushButton#leaveBtn:hover   { background-color: #cb4335; }
    QPushButton#leaveBtn:pressed { background-color: #b03a2e; }
    QPushButton#leaveBtn:disabled {
        background-color: #4a6278;
        color: #bdc3c7;
    }

    /* ── Dialogs / forms ─────────────────────────────────── */
    QDialog { background-color: #2c3e50; }
    QLabel  { color: #ecf0f1; font-size: 13px; }
    QLineEdit, QTextEdit {
        background-color: #1a252f;
        color: #ecf0f1;
        border: 1px solid #4a6278;
        border-radius: 4px;
        padding: 6px 8px;
        font-size: 13px;
    }
    QLineEdit:focus, QTextEdit:focus { border-color: #3498db; }

    QPushButton#createBtn {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 7px 18px;
        font-size: 13px;
    }
    QPushButton#createBtn:hover  { background-color: #2980b9; }
    QPushButton#createBtn:disabled {
        background-color: #4a6278;
        color: #bdc3c7;
    }
    QPushButton#cancelBtn {
        background-color: transparent;
        color: #bdc3c7;
        border: 1px solid #4a6278;
        border-radius: 4px;
        padding: 7px 18px;
        font-size: 13px;
    }
    QPushButton#cancelBtn:hover { background-color: #34495e; }
"""