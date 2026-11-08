# Actual initial environment failures
2026-11-08, this task's command results. No credential or software setting changed.

- `freecad --version`: no DISPLAY; Qt error `qt.qpa.xcb: could not connect to display`; `Could not load the Qt platform plugin "xcb"`; process aborted. Wrapper continued to Blender so its aggregate exit was not the FreeCAD status.
- `QT_QPA_PLATFORM=offscreen freecad --version`: exit1, `Program received signal SIGSEGV, Segmentation fault.` Stack included `libpython3.13.so.1.0(Py_EncodeLocale+0x57)`.
- Embedded `/usr/bin/python3`: FreeCAD1.0 import and document operations succeeded. `Part.makeCompound` minimal call exited1 without Python exception; `Part.Compound` succeeded. Use `Part.Compound` in generator. Root cause UNKNOWN, no claim software fault was repaired.
- TechDraw initial template copy failed: `Cannot copy file .../template.svg to /template.svg`. Captured original result in `freecad-initial-techdraw-failure.json`. Embedded document's TransientDir was empty. Explicit unique writable `/tmp/palisade-techdraw-*` directory corrected this call. Headless page creation/projectToSVG/save/reopen succeeded thereafter.

GUI manipulation of FreeCAD/Blender: NOT_TESTED. Headless Python FreeCAD and Blender background operations are separately recorded, not GUI proof.
