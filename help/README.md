# Help Documentation

This directory contains the help documentation for the Advanced Search Panel QGIS plugin.

## Structure

```
help/
├── source/
│   ├── index.html          # Main help documentation
│   ├── default.css         # Stylesheet for help pages
│   └── img/                # Directory for screenshots and images
├── help.py                 # Help system integration module
└── README.md               # This file
```

## Documentation Standards

The help documentation follows QGIS plugin help standards:

### HTML Structure
- **index.html**: Main documentation page with complete user guide
- **CSS Styling**: Uses QGIS-compatible styling with green color scheme
- **Responsive Design**: Works on different screen sizes
- **Print Friendly**: Includes print styles for documentation

### Content Organization
1. **Overview**: Plugin introduction and key features
2. **Installation**: Step-by-step installation instructions
3. **Getting Started**: Basic usage guide
4. **Configuration**: Detailed configuration options
5. **Templates**: API provider templates documentation
6. **Import/Export**: Configuration backup and sharing
7. **Advanced Features**: Power user functionality
8. **Troubleshooting**: Common issues and solutions

### Integration
- **Menu Integration**: Help menu item added to QGIS plugin menu
- **Context Help**: Can be accessed from within the plugin
- **Fallback Options**: Online documentation links when local help unavailable

## Adding Screenshots

To add screenshots to the documentation:

1. Save images in the `help/source/img/` directory
2. Use descriptive filenames (e.g., `configuration-dialog.png`)
3. Reference in HTML: `<img src="img/configuration-dialog.png" alt="Configuration Dialog" />`
4. Keep images optimized for web (< 200KB each)

## Updating Documentation

When updating the help documentation:

1. Edit `help/source/index.html`
2. Update version numbers and feature lists
3. Add new sections for new features
4. Update screenshots if UI changes
5. Test help integration in QGIS

## Localization

For future localization support:
- Keep text in separate sections for easy translation
- Use CSS for styling, not inline styles
- Consider creating subdirectories for different languages (e.g., `en/`, `de/`, `fr/`)

## Testing

To test the help system:
1. Load the plugin in QGIS
2. Access help via the plugin menu
3. Verify all links work
4. Check formatting on different screen sizes
5. Test print functionality

## Online Documentation

If local help is unavailable, the system falls back to:
- GitHub repository README
- Online documentation (when available)
- Plugin repository page