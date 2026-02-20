import fs from 'node:fs';
import path from 'node:path';

const rootDir = path.resolve(process.cwd(), '..');
const envPath = path.join(rootDir, '.env');

function parseEnvFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const values = {};

  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) {
      continue;
    }

    const separatorIndex = line.indexOf('=');
    if (separatorIndex === -1) {
      continue;
    }

    const key = line.slice(0, separatorIndex).trim();
    const value = line.slice(separatorIndex + 1).trim();
    values[key] = value;
  }

  return values;
}

const fileEnv = parseEnvFile(envPath);
const env = { ...fileEnv, ...process.env };

const specs = [
  { key: 'OPENAI_API_KEY', required: false, message: 'Nur erforderlich, wenn OPENAI-Features genutzt werden.' },
  { key: 'OPENAI_MODEL', required: false, message: 'Optional, Default ist gpt-4o-mini.' },
  { key: 'ALLOWED_ORIGINS', required: true, message: 'Erforderlich für CORS-Konfiguration.' },
  { key: 'USE_OPENAI_CHART', required: false, message: 'Optional, 1 = OpenAI-Chartanalyse aktiv.' },
  { key: 'PORT', required: false, message: 'Optional, Default ist 8787.' }
];

let errorCount = 0;
let warningCount = 0;

console.log(`Prüfe Umgebungsvariablen (${envPath})...`);
if (!fs.existsSync(envPath)) {
  warningCount += 1;
  console.warn('⚠️  Keine .env im Repo-Root gefunden. Es werden nur Prozess-Umgebungsvariablen geprüft.');
}

for (const spec of specs) {
  const value = env[spec.key];
  const hasValue = typeof value === 'string' && value.trim().length > 0;

  if (spec.required && !hasValue) {
    errorCount += 1;
    console.error(`❌ ${spec.key} fehlt. ${spec.message}`);
    continue;
  }

  if (!spec.required && !hasValue) {
    warningCount += 1;
    console.warn(`⚠️  ${spec.key} ist nicht gesetzt. ${spec.message}`);
    continue;
  }

  console.log(`✅ ${spec.key} ist gesetzt.`);
}

const useOpenAIChart = (env.USE_OPENAI_CHART || '').trim() === '1';
const hasApiKey = typeof env.OPENAI_API_KEY === 'string' && env.OPENAI_API_KEY.trim().length > 0;
if (useOpenAIChart && !hasApiKey) {
  errorCount += 1;
  console.error('❌ USE_OPENAI_CHART=1 benötigt OPENAI_API_KEY, aber OPENAI_API_KEY fehlt.');
}

if (errorCount > 0) {
  console.error(`\nPrüfung fehlgeschlagen: ${errorCount} Fehler, ${warningCount} Warnungen.`);
  process.exit(1);
}

console.log(`\nPrüfung abgeschlossen: 0 Fehler, ${warningCount} Warnungen.`);
