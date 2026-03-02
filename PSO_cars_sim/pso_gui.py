import customtkinter as ctk
import numpy as np
import io

import matplotlib
matplotlib.use("Agg")  
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.transforms as transforms

from PIL import Image
import pso_module as pso


# ---------- helpers: cars as little boxes ----------
def car_corners(x, y, psi, L=0.9, W=0.45):
    # Rectangle centered at (0,0), then rotate+translate
    c = np.cos(psi)
    s = np.sin(psi)
    R = np.array([[c, -s], [s, c]])
    corners = np.array([
        [-L/2, -W/2],
        [ L/2, -W/2],
        [ L/2,  W/2],
        [-L/2,  W/2],
        [-L/2, -W/2],
    ])
    pts = (corners @ R.T) + np.array([x, y])
    return pts


class PSOGui(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PSO Cars GUI (Plot as Image)")
        self.geometry("1100x800")

        # ---- sim params ----
        self.running = False
        self.dt = 0.05
        self.velocity = 1.0
        self.ncars = 3

        # ---- main layout ----
        self.plot_frame = ctk.CTkFrame(self)
        self.plot_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.panel = ctk.CTkFrame(self)
        self.panel.pack(fill="x", padx=10, pady=(0, 10))

        # ---- image label (this is where the "plot picture" goes) ----
        self.img_label = ctk.CTkLabel(self.plot_frame, text="")
        self.img_label.pack(fill="both", expand=True)

        # ---- create cars ----
        self.cars = []
        self.controls = []
        self.trajs = []
        self.create_swarm(self.ncars)
        self.set_velocity(self.velocity)

        # ---- controls ----
        ctk.CTkButton(self.panel, text="Start", command=self.start).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(self.panel, text="Stop", command=self.stop).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(self.panel, text="Step once", command=self.step_once).pack(side="left", padx=10, pady=10)

        # Velocity slider
        self.v_label = ctk.CTkLabel(self.panel, text=f"Velocity: {self.velocity:.2f} m/s")
        self.v_label.pack(side="left", padx=(25, 6))
        self.v_slider = ctk.CTkSlider(self.panel, from_=0.0, to=5.0, number_of_steps=100, command=self.on_velocity)
        self.v_slider.set(self.velocity)
        self.v_slider.pack(side="left", padx=10)

        # Number of cars slider
        self.n_label = ctk.CTkLabel(self.panel, text=f"Cars: {self.ncars}")
        self.n_label.pack(side="left", padx=(25, 6))
        self.n_slider = ctk.CTkSlider(self.panel, from_=1, to=20, number_of_steps=19, command=self.on_ncars)
        self.n_slider.set(self.ncars)
        self.n_slider.pack(side="left", padx=10)

        # initial render
        self.render_plot_image()

    # ---------- swarm ----------
    def create_swarm(self, ncars: int):
        self.cars = []
        self.controls = []
        self.trajs = [[] for _ in range(ncars)]

        xs = np.linspace(-6, 6, ncars)
        ys = np.linspace(-3, 3, ncars)
        psis = np.linspace(0.0, 1.2, ncars)

        for i in range(ncars):
            car = pso.Car(pso.State(float(xs[i]), float(ys[i]), float(psis[i])), 1.0, 2.5)
            self.cars.append(car)
            u = pso.Control()
            u.delta = 0.0
            u.a = 0.0
            self.controls.append(u)

    def set_velocity(self, v: float):
        self.velocity = float(v)
        for car in self.cars:
            car.setVelocity(self.velocity)

    # ---------- slider callbacks ----------
    def on_velocity(self, val):
        self.set_velocity(float(val))
        self.v_label.configure(text=f"Velocity: {self.velocity:.2f} m/s")
        self.render_plot_image()

    def on_ncars(self, val):
        new_n = int(round(float(val)))
        if new_n == self.ncars:
            return
        self.ncars = new_n
        self.n_label.configure(text=f"Cars: {self.ncars}")
        self.running = False
        self.create_swarm(self.ncars)
        self.set_velocity(self.velocity)
        self.render_plot_image()

    # ---------- sim loop ----------
    def start(self):
        if not self.running:
            self.running = True
            self.after(30, self.loop)

    def stop(self):
        self.running = False

    def loop(self):
        if not self.running:
            return
        self.step_once()
        self.after(30, self.loop)

    def step_once(self):
        # demo steering — replace with PSO outputs if you want
        for i, u in enumerate(self.controls):
            u.delta = 0.08 * np.sin(0.25 * i)
            u.a = 0.0

        for i, car in enumerate(self.cars):
            car.step(self.controls[i], self.dt)
            x, y, psi = car.getPos()
            self.trajs[i].append((x, y, psi))

        self.render_plot_image()

    # ---------- render matplotlib -> image -> CTkLabel ----------
    def render_plot_image(self):
        # Make a figure OFFSCREEN (Agg backend)
        fig = plt.figure(figsize=(9, 6), dpi=120)
        ax = fig.add_subplot(111)
        ax.set_aspect("equal")
        ax.grid(True)
        ax.set_xlim(-10, 10)
        ax.set_ylim(-10, 10)
        ax.set_title("Swarm cars (rendered image in CTk)")

        cmap = plt.cm.tab20

        for i in range(len(self.cars)):
            if len(self.trajs[i]) == 0:
                x, y, psi = self.cars[i].getPos()
            else:
                x, y, psi = self.trajs[i][-1]

            # trajectory line
            if len(self.trajs[i]) >= 2:
                traj = np.array(self.trajs[i])
                ax.plot(traj[:, 0], traj[:, 1], linewidth=1)

            # car box
            pts = car_corners(x, y, psi, L=0.9, W=0.45)
            ax.plot(pts[:, 0], pts[:, 1], linewidth=2)

        # Render to PNG bytes
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)

        # Convert to CTkImage and show
        pil_img = Image.open(buf)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
        self.img_label.configure(image=ctk_img)
        self.img_label.image = ctk_img  # keep reference


def main():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("green")
    app = PSOGui()
    app.mainloop()


if __name__ == "__main__":
    main()