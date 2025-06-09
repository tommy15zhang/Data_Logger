# Datalogger Project Architecture Diagram

```mermaid
graph TD
    A[main.py\nEntry point] --> B[gui.py\nMainWindow GUI\nSerial, Plots, Plant Logic]
    B --> C[widgets.py\nCustom PyQt5 Widgets]
    B --> D[plant_preferences.json\nPlant Data]
    B --> E[serial_handler.py\nSerial Abstraction (optional)]
    
    subgraph Project Root
        F[requirements.txt\nDependencies]
        G[README.md\nDocumentation]
    end
    
    subgraph src/
        A
        B
        C
        D
        E
    end
```

- **main.py**: Starts the application, shows the main window.
- **gui.py**: Main GUI logic, handles serial, plotting, plant selection, and analysis.
- **widgets.py**: Custom widgets for displaying metrics and advice.
- **serial_handler.py**: (Optional) Serial port abstraction.
- **plant_preferences.json**: Plant data and environmental preferences.
- **requirements.txt**: Python dependencies.
- **README.md**: Project documentation.

> You can copy this Mermaid code into [mermaid.live](https://mermaid.live/) or compatible Markdown viewers to generate a graphical flow chart for your report.
