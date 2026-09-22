# Nuki Berechtigungsverwaltung

Ergänzt `hass_nuki_ng` um lokale, versionierte Sicherungen und bearbeitbare
Berechtigungsdaten.

## Sicherheit

- API-Token und PIN-Ziffern werden niemals gespeichert.
- Vor jeder Änderung oder Löschung wird automatisch gesichert.
- Änderungen werden anschließend erneut von Nuki gelesen und verifiziert.
- Es werden höchstens 90 Sicherungsstände in Home Assistants geschütztem
  `.storage`-Bereich aufbewahrt.

Die Nuki-API gibt bestehende PIN-Ziffern nicht zurück. Deshalb lassen sich
Namen, Status und Zeitregeln sichern, bestehende PINs jedoch nicht exportieren
oder wiederherstellen.
