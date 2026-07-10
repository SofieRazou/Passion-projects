self.stability_title = QLabel("Bode Plot and Stability Analysis")
        self.stability_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.stability_title.setObjectName("stabilityTitle")

        self.stability_plot = QLabel()
        self.stability_plot.setObjectName("stabilityImage")
        self.stability_plot.setMinimumSize(600, 450)
        self.stability_plot.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.stability_layout.addWidget(self.stability_title)
        self.stability_layout.addWidget(
            self.stability_plot,
            stretch=1
        )

        # Get an absolute path that QSS can reliably understand
        bode_path = Path(BODE_FILE).resolve().as_posix()
