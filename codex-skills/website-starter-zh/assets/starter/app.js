"use strict";

// Everything is local. No storage, network requests, or user HTML are used.
(() => {
  const courseButtons = [...document.querySelectorAll("[data-course]")];
  const lessons = [...document.querySelectorAll(".lesson")];
  const completionInputs = [...document.querySelectorAll("[data-complete]")];

  function selectCourse(name, moveFocus) {
    courseButtons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.course === name));
    });
    lessons.forEach((lesson) => {
      lesson.hidden = lesson.id !== `lesson-${name}`;
    });
    const heading = document.getElementById(`heading-${name}`);
    document.getElementById("course-status").textContent = `已切换课程：${heading.textContent}`;
    if (moveFocus) heading.focus();
  }

  courseButtons.forEach((button) => {
    button.disabled = false;
    button.addEventListener("click", () => selectCourse(button.dataset.course, true));
  });
  selectCourse("html", false);

  completionInputs.forEach((input) => {
    input.disabled = false;
    input.checked = false;
    input.addEventListener("change", () => {
      const checked = completionInputs.filter((item) => item.checked).length;
      document.getElementById("study-status").textContent = `本页已勾选 ${checked} / 3 课`;
    });
  });

  const readyButton = document.getElementById("ready");
  readyButton.disabled = false;
  readyButton.addEventListener("click", () => {
    document.getElementById("message").textContent = "书已备好，周三见！";
  });

  const keyword = document.getElementById("keyword");
  const topic = document.getElementById("topic");
  const clearButton = document.getElementById("clear-filters");
  const knowledgeItems = [...document.querySelectorAll(".knowledge-item")];
  const filterStatus = document.getElementById("filter-status");

  function filterKnowledge() {
    const query = keyword.value.trim().toLocaleLowerCase();
    let visible = 0;
    knowledgeItems.forEach((item) => {
      const matchesTopic = topic.value === "all" || item.dataset.topic === topic.value;
      const matchesText = item.textContent.toLocaleLowerCase().includes(query);
      item.hidden = !(matchesTopic && matchesText);
      if (!item.hidden) visible += 1;
    });
    filterStatus.textContent = `显示 ${visible} 条知识`;
    document.getElementById("empty-state").hidden = visible !== 0;
  }

  function clearFilters() {
    keyword.value = "";
    topic.value = "all";
    filterKnowledge();
    keyword.focus();
  }

  [keyword, topic, clearButton].forEach((control) => { control.disabled = false; });
  keyword.value = "";
  topic.value = "all";
  keyword.addEventListener("input", filterKnowledge);
  topic.addEventListener("change", filterKnowledge);
  clearButton.addEventListener("click", clearFilters);
  document.getElementById("empty-clear").addEventListener("click", clearFilters);
  document.getElementById("search-form").addEventListener("submit", (event) => {
    event.preventDefault();
    filterKnowledge();
  });
  filterKnowledge();

  const quiz = document.getElementById("quiz-form");
  const quizResult = document.getElementById("quiz-result");
  const questions = [
    { name: "q1", answer: "a", explanation: "正确答案是 A。p 用于段落；h1 表示页面主标题，button 表示可操作的按钮。" },
    { name: "q2", answer: "b", explanation: "正确答案是 B。padding 是内边距，控制内容到边框的距离；margin 控制框外距离，color 控制文字颜色。" },
    { name: "q3", answer: "c", explanation: "正确答案是 C。addEventListener 将点击事件与函数连接起来；背景色和类名本身不会建立事件监听。" }
  ];
  let hasFeedback = false;

  function clearQuizFeedback() {
    questions.forEach(({ name }) => {
      const feedback = document.getElementById(`feedback-${name}`);
      feedback.hidden = true;
      feedback.textContent = "";
      delete feedback.dataset.state;
      const fieldset = quiz.querySelector(`[data-question="${name}"]`);
      fieldset.removeAttribute("aria-describedby");
    });
    hasFeedback = false;
  }

  quiz.reset();
  quiz.querySelectorAll("input, button").forEach((control) => { control.disabled = false; });
  quiz.addEventListener("submit", (event) => {
    event.preventDefault();
    clearQuizFeedback();
    const missing = questions.filter(({ name }) => !quiz.querySelector(`input[name="${name}"]:checked`));
    if (missing.length) {
      missing.forEach(({ name }) => {
        const feedback = document.getElementById(`feedback-${name}`);
        feedback.textContent = "尚未选择：请为这道题选择一个答案。";
        feedback.dataset.state = "missing";
        feedback.hidden = false;
        quiz.querySelector(`[data-question="${name}"]`).setAttribute("aria-describedby", feedback.id);
      });
      quizResult.textContent = `还有 ${missing.length} 题未作答，补选后再检查答案。`;
      quiz.querySelector(`input[name="${missing[0].name}"]`).focus();
      hasFeedback = true;
      return;
    }
    let correct = 0;
    questions.forEach(({ name, answer, explanation }) => {
      const selected = quiz.querySelector(`input[name="${name}"]:checked`);
      const isCorrect = selected.value === answer;
      if (isCorrect) correct += 1;
      const feedback = document.getElementById(`feedback-${name}`);
      feedback.textContent = `${isCorrect ? "答对了。" : "这题还需要再看一看。"} ${explanation}`;
      feedback.dataset.state = isCorrect ? "correct" : "incorrect";
      feedback.hidden = false;
      quiz.querySelector(`[data-question="${name}"]`).setAttribute("aria-describedby", feedback.id);
    });
    quizResult.textContent = `本次答对 ${correct} / 3 题。${correct === 3 ? "三题都答对了，试着把例子改成自己的作品。" : "逐题看看解释，再回到对应课程练习。"}`;
    quizResult.focus();
    hasFeedback = true;
  });
  quiz.addEventListener("change", () => {
    if (hasFeedback) {
      clearQuizFeedback();
      quizResult.textContent = "答案已修改，请再次点击“检查答案”。";
    }
  });
  quiz.addEventListener("reset", () => {
    clearQuizFeedback();
    quizResult.textContent = "已重置：三道题已清空，可以重新练习。";
    quiz.querySelector('input[name="q1"]').focus();
  });
})();
