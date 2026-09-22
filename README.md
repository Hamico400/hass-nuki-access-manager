# Nuki Berechtigungsverwaltung für Home Assistant

Private Home-Assistant-Erweiterung für die sichere Verwaltung der vorhandenen
Nuki-Berechtigungen über die bereits eingerichtete `hass_nuki_ng`-Integration.

## Funktionen

- tägliche und manuelle Sicherung der Zugangs-Metadaten
- automatische Sicherung vor jeder Änderung oder Löschung
- bis zu 90 lokale Sicherungsstände
- Namen und Fernzugriffsfreigaben direkt als Home-Assistant-Entitäten
- Anlage neuer Keypad-Zugänge und kontrolliertes Löschen über Aktionen
- erneutes Lesen und Prüfen nach Änderungen

## Datenschutz

API-Token und PIN-Ziffern werden weder gespeichert noch in GitHub übertragen.
Nuki stellt bestehende PIN-Ziffern über seine API nicht bereit; daher können
diese nicht exportiert oder wiederhergestellt werden.
