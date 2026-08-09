(() => {
  'use strict';

  const banner = document.querySelector('[data-analytics-consent]');
  if (!banner) return;

  const counterId = Number.parseInt(banner.dataset.counterId, 10);
  if (!Number.isSafeInteger(counterId) || counterId <= 0) return;

  const consentKey = 'mgroup_analytics_consent_v1';
  let initialized = false;
  const readConsent = () => {
    try { return window.localStorage.getItem(consentKey); } catch (error) { return null; }
  };
  const saveConsent = (value) => {
    try { window.localStorage.setItem(consentKey, value); } catch (error) {
      // Consent remains valid for the current page when storage is unavailable.
    }
  };
  const initializeMetrika = () => {
    if (initialized) return;
    initialized = true;
    window.ym = window.ym || function () {
      (window.ym.a = window.ym.a || []).push(arguments);
    };
    window.ym.l = Date.now();
    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://mc.yandex.ru/metrika/tag.js';
    document.head.appendChild(script);
    window.ym(counterId, 'init', {
      accurateTrackBounce: true,
      clickmap: false,
      sendTitle: true,
      trackLinks: true,
      webvisor: false,
    });
  };
  window.trackMetrikaGoal = (goalName) => {
    if (readConsent() !== 'granted' || typeof goalName !== 'string') return;
    initializeMetrika();
    window.ym(counterId, 'reachGoal', goalName);
  };
  banner.querySelector('[data-analytics-accept]').addEventListener('click', () => {
    saveConsent('granted');
    banner.hidden = true;
    initializeMetrika();
  });
  banner.querySelector('[data-analytics-reject]').addEventListener('click', () => {
    saveConsent('denied');
    banner.hidden = true;
  });
  const consent = readConsent();
  if (consent === 'granted') initializeMetrika();
  else if (consent !== 'denied') banner.hidden = false;
  document.querySelectorAll('[data-metrika-goal]').forEach((element) => {
    window.trackMetrikaGoal(element.dataset.metrikaGoal);
  });
})();
