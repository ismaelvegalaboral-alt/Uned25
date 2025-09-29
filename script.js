const studyForm = document.querySelector('.study-form');
const planOutput = document.querySelector('.plan-output');
const demoBox = document.querySelector('.demo');

const createPlan = (hours, subjects) => {
  const subjectList = subjects
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  if (!subjectList.length) {
    return 'Añade al menos una materia para generar tu plan.';
  }

  const totalHours = Math.max(1, Math.min(80, hours));
  const weeklySessions = 5;
  const hoursPerSubject = (totalHours / subjectList.length).toFixed(1);

  const sessions = subjectList.map((subject, index) => {
    const focus = index % 2 === 0 ? 'repaso activo' : 'ejercicios prácticos';
    return `• ${subject}: ${hoursPerSubject}h con ${focus}`;
  });

  return `Plan sugerido (${totalHours}h/semana):\n${sessions.join('\n')}\nReserva 2h extra para simulacros y análisis de errores.`;
};

if (studyForm) {
  studyForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const hours = Number(document.querySelector('#hours').value || 10);
    const subjects = document.querySelector('#subjects').value || '';
    const plan = createPlan(hours, subjects);
    planOutput.textContent = plan;
  });
}

const toolTemplates = {
  summary: `Resumen inteligente generado:\n- Tesis central identificada\n- 3 conceptos clave explicados con ejemplos\n- Pregunta de repaso sugerida para profundizar`,
  flashcards: `Flashcards creadas:\n1. Definición clave → respuesta oculta\n2. Fórmula esencial → explicación práctica\n3. Pregunta corta → pista de memoria activa`,
  quiz: `Quiz adaptativo listo:\n• 5 preguntas nivel básico\n• 3 preguntas nivel intermedio\n• 2 preguntas retadoras con feedback instantáneo`
};

if (demoBox) {
  document.querySelectorAll('[data-action]').forEach((button) => {
    button.addEventListener('click', () => {
      const action = button.dataset.action;
      const template = toolTemplates[action];
      demoBox.textContent = template || 'Próximamente más herramientas mágicas ✨';
    });
  });
}

const dropzone = document.querySelector('.upload__dropzone');

if (dropzone) {
  const input = dropzone.querySelector('input[type="file"]');

  dropzone.addEventListener('click', () => input.click());

  dropzone.addEventListener('dragover', (event) => {
    event.preventDefault();
    dropzone.classList.add('is-dragging');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('is-dragging');
  });

  dropzone.addEventListener('drop', (event) => {
    event.preventDefault();
    dropzone.classList.remove('is-dragging');
    input.files = event.dataTransfer.files;
    const files = Array.from(event.dataTransfer.files).map((file) => file.name).join(', ');
    demoBox.textContent = `Transformaremos estos archivos en magia de estudio:\n${files}`;
  });
}
