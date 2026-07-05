# Robot Arm Simulator

>A planar inverse kinematics visualiser for 2-DOF, 3-DOF and 4-DOF robotic arms, built with Python and PyQt5.

*Developed by [Ranasurya Ghosh](https://github.com/NuclearVenom)*

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/downloads/release/python-3130/)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-BA55D3?style=flat&logo=qt&logoColor=white)
[![LICENSE](https://img.shields.io/badge/LICENSE-MIT-green?style=flat&logo=data:image/svg%2Bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0iI2ZmZiIgZD0iTTEyLjc1IDIuNzVWNC41aDEuOTc1Yy4zNTEgMCAuNjk0LjEwNi45ODQuMzAzbDEuNjk3IDEuMTU0Yy4wNDEuMDI4LjA5LjA0My4xNC4wNDNoNC4xMDJhLjc1Ljc1IDAgMCAxIDAgMS41SDIwLjA3bDMuMzY2IDcuNjhhLjc0OS43NDkgMCAwIDEtLjIzLjg5NmMtLjEuMDc0LS4yMDMuMTQzLS4zMS4yMDZhNi4yOTYgNi4yOTYgMCAwIDEtLjc5LjM5OSA3LjM0OSA3LjM0OSAwIDAgMS0yLjg1Ni41NjkgNy4zNDMgNy4zNDMgMCAwIDEtMi44NTUtLjU2OCA2LjIwNSA2LjIwNSAwIDAgMS0uNzktLjQgMy4yMDUgMy4yMDUgMCAwIDEtLjMwNy0uMjAybC0uMDA1LS4wMDRhLjc0OS43NDkgMCAwIDEtLjIzLS44OTZsMy4zNjgtNy42OGgtLjg4NmMtLjM1MSAwLS42OTQtLjEwNi0uOTg0LS4zMDNsLTEuNjk3LTEuMTU0YS4yNDYuMjQ2IDAgMCAwLS4xNC0uMDQzSDEyLjc1djE0LjVoNC40ODdhLjc1Ljc1IDAgMCAxIDAgMS41SDYuNzYzYS43NS43NSAwIDAgMSAwLTEuNWg0LjQ4N1Y2SDkuMjc1YS4yNDkuMjQ5IDAgMCAwLS4xNC4wNDNMNy40MzkgNy4xOTdjLS4yOS4xOTctLjYzMy4zMDMtLjk4NC4zMDNoLS44ODZsMy4zNjggNy42OGEuNzUuNzUgMCAwIDEtLjIwOS44NzhjLS4wOC4wNjUtLjE2LjEyNi0uMzEuMjIzYTYuMDc3IDYuMDc3IDAgMCAxLS43OTIuNDMzIDYuOTI0IDYuOTI0IDAgMCAxLTIuODc2LjYyIDYuOTEzIDYuOTEzIDAgMCAxLTIuODc2LS42MiA2LjA3NyA2LjA3NyAwIDAgMS0uNzkyLS40MzMgMy40ODMgMy40ODMgMCAwIDEtLjMwOS0uMjIxLjc2Mi43NjIgMCAwIDEtLjIxLS44OEwzLjkzIDcuNUgyLjM1M2EuNzUuNzUgMCAwIDEgMC0xLjVoNC4xMDJjLjA1IDAgLjA5OS0uMDE1LjE0MS0uMDQzbDEuNjk1LTEuMTU0Yy4yOS0uMTk4LjYzNC0uMzAzLjk4NS0uMzAzaDEuOTc0VjIuNzVhLjc1Ljc1IDAgMCAxIDEuNSAwWk0yLjE5MyAxNS4xOThhNS40MTQgNS40MTQgMCAwIDAgMi41NTcuNjM1IDUuNDE0IDUuNDE0IDAgMCAwIDIuNTU3LS42MzVMNC43NSA5LjM2OFptMTQuNTEtLjAyNGMuMDgyLjA0LjE3NC4wODMuMjc1LjEyNi41My4yMjMgMS4zMDUuNDUgMi4yNzIuNDVhNS44NDcgNS44NDcgMCAwIDAgMi41NDctLjU3NkwxOS4yNSA5LjM2N1oiLz48L3N2Zz4=)](./LICENSE)
---

![Demo](assets/demo.gif)
<br><br>

## Overview

[Robot Arm Simulator](https://github.com/NuclearVenom/Robot-Arm-Simulator-(2D)) is an interactive desktop application that visualises how robotic arms solve the inverse kinematics problem in two-dimensional space. You click anywhere on the canvas, and the arm smoothly animates to that position — computing the required joint angles in real time using classical geometric methods.

The simulator supports three configurations: a two-joint arm (2-DOF), a three-joint arm (3-DOF), and a four-joint arm (4-DOF). You can switch between them live, watching the arm morph between configurations. A step-by-step calculation report can be exported for any target position, making the simulator as useful for learning as it is for experimentation.

---

## Features

| Feature | Description |
|---|---|
| 2-DOF / 3-DOF / 4-DOF modes | Switch between configurations using an animated segmented toggle. The arm morphs smoothly between them. |
| Click-to-target IK | Click anywhere on the canvas to set a target. The arm animates to reach it. |
| Real-time joint readout | Shoulder, elbow, wrist and finger angles update every frame in degrees. |
| End-effector position display | Live X/Y coordinates of the tip of the arm in world units. |
| Adjustable link lengths | Sliders for all four link lengths (L₁ through L₄), with relevant sliders enabled or greyed out per mode. |
| Adjustable animation speed | Control how fast the arm moves from 1 % to 100 %. |
| Workspace visualisation | A shaded circle shows the maximum reachable envelope, updating as link lengths change. |
| Step-by-step calculation report | Generates a full textbook-style derivation of the IK solution for the current target. Copy to clipboard or download as a `.txt` file. |
| Hover coordinate display | Shows the world-space coordinates of your mouse cursor on the canvas. |
| Reset button | Animates all joints back to zero degrees. |

---

## Installation

**Requirements**

- Python 3.10 or later
- PyQt5

**Install dependencies**

```bash
pip install PyQt5
```

**Run the application**

```bash
python run_simulation.py
```

The window opens maximised. No additional configuration is needed.

---

## How to Use

### Setting a Target

Click anywhere on the canvas. The arm will compute the required joint angles and animate smoothly to that position. If the target is outside the arm's reach, a red error message is shown and the arm does not move.

### Switching Modes

Use the **2-DOF / 3-DOF / 4-DOF** toggle in the sidebar. The arm morphs between configurations over a short animation. During morphing, target input is temporarily paused.

### Adjusting Link Lengths

The **Link Lengths** section provides sliders for each link, measured in world units (u). L₃ becomes editable in 3-DOF mode; L₄ becomes editable in 4-DOF mode. Changing a link length clears the current target and updates the workspace boundary.

### Viewing the Calculation

After clicking a target, press **Show Calculation**. A floating window displays the complete inverse kinematics derivation for the current mode, including all intermediate values, a forward kinematics verification, and the residual error. Use **Copy to clipboard** or **Download text file** to save it.

### Resetting the Arm

Press **Reset Arm** to animate all joints back to θ = 0°.

---

## The Mathematics — A Guided Explanation

The central problem this simulator solves is called **inverse kinematics (IK)**. Before explaining it, it helps to understand the simpler, opposite problem.

---

### Forward Kinematics: From Angles to Position

Given the joint angles, where does the tip of the arm end up?

This is straightforward geometry. Think of each link as a line segment. The shoulder joint is fixed at the origin. If the shoulder rotates by angle θ₁ and the upper arm has length L₁, then the elbow position is:

```
Elbow_x = L₁ · cos(θ₁)
Elbow_y = L₁ · sin(θ₁)
```

Adding the forearm (length L₂, at cumulative angle θ₁ + θ₂):

```
Wrist_x = Elbow_x + L₂ · cos(θ₁ + θ₂)
Wrist_y = Elbow_y + L₂ · sin(θ₁ + θ₂)
```

Each additional link follows the same pattern, accumulating angles. Forward kinematics is always a clean, direct calculation with a unique answer.

---

### Inverse Kinematics: From Position to Angles

Inverse kinematics asks the reverse question: given a desired tip position (Pₓ, Pᵧ), what angles θ₁, θ₂, … are required?

This is much harder. There may be zero solutions (the point is unreachable), exactly one, or infinitely many. The approach varies by the number of joints.

---

### 2-DOF: Closed-Form Geometric Solution

A two-link planar arm has a unique, analytic solution. It uses the **Law of Cosines** from triangle geometry.

**Step 1 — Distance to target:**

```
r = √(Pₓ² + Pᵧ²)
```

This is the straight-line distance from the base to the target.

**Step 2 — Reachability check:**

The arm can only reach the target if:

```
|L₁ − L₂|  ≤  r  ≤  L₁ + L₂
```

The upper bound is when both links are fully extended. The lower bound is when one link folds back against the other.

**Step 3 — Elbow angle (Law of Cosines):**

The base, elbow, and target form a triangle with sides L₁, L₂, and r. The Law of Cosines gives:

```
cos(θ₂) = (r² − L₁² − L₂²) / (2 · L₁ · L₂)
θ₂ = arccos(result)
```

**Step 4 — Shoulder angle:**

```
α = atan2(Pᵧ, Pₓ)           — angle toward the target
β = atan2(L₂·sin θ₂, L₁ + L₂·cos θ₂)   — angle offset from elbow
θ₁ = α − β
```

This yields the elbow-up configuration. There is a second valid solution (elbow-down) using −θ₂, which the simulator selects against by minimising joint displacement from the current pose.

---

### 3-DOF: φ-Sweep (Orientation Sampling)

A three-link arm is **kinematically redundant** — there are infinitely many angle combinations that place the tip at the same point. A human arm is a familiar example: you can touch a point in front of you while rotating your wrist into countless orientations.

The extra joint introduces a free parameter: the end-effector orientation φ = θ₁ + θ₂ + θ₃ (the direction in which the last link points).

**The algorithm:**

1. Sweep φ over 360 candidate values between −π and +π.
2. For each φ, the wrist joint must lie at:
   ```
   Wₓ = Pₓ − L₃ · cos(φ)
   Wᵧ = Pᵧ − L₃ · sin(φ)
   ```
   (back-projecting from the target along the final link direction)
3. Solve the 2-DOF sub-problem for (Wₓ, Wᵧ) using L₁ and L₂.
4. Recover θ₃ = φ − θ₁ − θ₂.
5. Keep the solution with the smallest total joint displacement from the current configuration — this makes the motion smooth and natural.

This approach trades closed-form elegance for generality. The sampling density (360 steps) is fine enough for smooth results in real time.

---

### 4-DOF: Double φψ-Sweep

A four-link arm introduces a second redundancy. Two free orientation parameters must be resolved:

- ψ = θ₁ + θ₂ + θ₃ + θ₄  — total end-effector orientation
- φ = θ₁ + θ₂ + θ₃       — sub-orientation at the finger joint

**The algorithm:**

1. Sweep ψ over 180 values.
2. For each ψ, compute the finger joint position by back-projecting along L₄:
   ```
   Fₓ = Pₓ − L₄ · cos(ψ)
   Fᵧ = Pᵧ − L₄ · sin(ψ)
   ```
3. Sweep φ over 180 values.
4. For each φ, compute the wrist centre by back-projecting along L₃:
   ```
   Wₓ = Fₓ − L₃ · cos(φ)
   Wᵧ = Fᵧ − L₃ · sin(φ)
   ```
5. Solve the 2-DOF sub-problem for (Wₓ, Wᵧ).
6. Recover θ₃ = φ − θ₁ − θ₂ and θ₄ = ψ − θ₁ − θ₂ − θ₃.
7. Keep the minimum-displacement solution.

The 4-DOF mode evaluates up to 180 × 180 × 2 = 64,800 candidate configurations per click. The simulator runs this in Python at interactive speeds because the geometry per candidate is extremely cheap.

---

### Verification

After computing any IK solution, the simulator runs forward kinematics on the result and measures the residual error — the distance between the computed end-effector position and the intended target. The calculation report shows this value. For the 2-DOF closed-form solver it is essentially zero (floating-point only). For the sweep-based solvers it is bounded by the angular resolution of the sweep.

---

## Real-World Relevance

This simulator models a class of problem that appears in many engineering domains.

**Industrial robot arms** — Manufacturing robots (welding, assembly, pick-and-place) must continuously solve IK as they follow programmed paths. The geometric techniques in this simulator are direct precursors to the methods used in industrial controllers.

**Computer animation and games** — Animating a character's hand to reach a door handle, or a foot to step on a surface, is an IK problem. The redundancy resolution strategy used here (minimising displacement from the current pose) is the same principle behind smooth motion in animation rigs.

**Surgical robotics** — Minimally invasive surgical robots operate inside the body through small incisions. Their slender, multi-link arms must reach precise targets within tight spatial constraints — exactly the workspace and reachability analysis visualised here.

**Prosthetics and exoskeletons** — Control systems for powered prosthetic limbs use IK to translate intended limb position into actuator commands across multiple joints.

**Autonomous vehicles and drones** — Robotic manipulators mounted on autonomous vehicles (for inspection, package delivery, or construction) rely on real-time IK to interact with their environment.

The 2-DOF mode is a teaching model for introductory robotics. The 3-DOF and 4-DOF modes demonstrate what redundancy means in practice — how extra degrees of freedom give a system more flexibility but require a more sophisticated control strategy.

---

## Project Structure

```
robot_arm_simulator.py   — Single-file application
README.md                — This document
```

All logic, UI, and rendering are contained in a single Python file organised into clearly separated classes:

| Class | Responsibility |
|---|---|
| `ArmCanvas` | Canvas widget. Handles painting, mouse input, forward and inverse kinematics, and animation stepping. |
| `MainWindow` | Main application window. Builds the sidebar UI, connects signals, manages the 30 fps timer. |
| `TriToggle` | Custom segmented-control toggle widget for DOF selection. |
| `LinkSlider` | Labelled slider row for adjusting individual link lengths. |
| `MetricRow` | Two-column label/value row used throughout the sidebar. |
| `SectionBox` | Styled `QGroupBox` container for sidebar sections. |
| `CalculationDialog` | Floating window for displaying, copying and saving the IK derivation. |


---

## Acknowledgements

Built entirely in Python using the PyQt5 GUI framework. No external robotics or mathematics libraries are used — all kinematics are implemented from first principles.

## License

MIT License — see [LICENSE](LICENSE) for details.
