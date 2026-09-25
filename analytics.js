/* SEND Lab: aggregate visit analytics. Preferences are explained in privacy.html. */
(function () {
  'use strict';
  var measurementId = 'G-DBN1XBSGQ8';
  var preferenceKey = 'send-lab-analytics-disabled';
  var browserOptOut = navigator.globalPrivacyControl === true ||
    navigator.doNotTrack === '1' || window.doNotTrack === '1';
  var storageAvailable = true;
  var optedOut = false;
  try {
    optedOut = localStorage.getItem(preferenceKey) === 'true';
  } catch (error) {
    storageAvailable = false;
  }
  var disabled = browserOptOut || optedOut || !storageAvailable;
  window['ga-disable-' + measurementId] = disabled;

  function clearAnalyticsCookies() {
    // Host-only cookies: never alter cookies belonging to another GitHub Pages site.
    document.cookie.split(';').forEach(function (cookie) {
      var name = cookie.trim().split('=')[0];
      if (name === '_ga' || name.indexOf('_ga_') === 0) {
        document.cookie = name + '=; Max-Age=0; Path=/; SameSite=Lax; Secure';
      }
    });
  }

  var status = document.getElementById('analytics-status');
  var toggle = document.getElementById('analytics-toggle');
  function updatePreferences() {
    if (!status || !toggle) return;
    if (browserOptOut) {
      status.textContent = '브라우저의 개인정보 보호 설정에 따라 통계 수집이 꺼져 있습니다. / Analytics is off because of your browser privacy settings.';
      toggle.hidden = true;
    } else if (!storageAvailable) {
      status.textContent = '이 브라우저에서 설정을 저장할 수 없어 통계 수집을 사용하지 않습니다. / Analytics is off because preferences cannot be stored.';
      toggle.hidden = true;
    } else {
      status.textContent = disabled ? '이 브라우저의 방문 통계 수집이 꺼져 있습니다. / Analytics is off in this browser.' : '이 브라우저의 방문 통계 수집이 켜져 있습니다. / Analytics is on in this browser.';
      toggle.textContent = disabled ? '방문 통계 허용 / Allow analytics' : '방문 통계 제외 / Opt out of analytics';
      toggle.hidden = false;
    }
  }
  updatePreferences();
  if (toggle) {
    toggle.addEventListener('click', function () {
      try {
        localStorage.setItem(preferenceKey, disabled ? 'false' : 'true');
        disabled = !disabled;
        window['ga-disable-' + measurementId] = disabled;
        if (disabled) clearAnalyticsCookies();
        updatePreferences();
      } catch (error) {
        storageAvailable = false;
        disabled = true;
        window['ga-disable-' + measurementId] = true;
        updatePreferences();
      }
    });
  }
  if (disabled) clearAnalyticsCookies();
  // Do not record local previews or visits to the privacy/preferences page.
  if (disabled || location.hostname !== 'deokjaeheo.github.io' ||
      location.pathname === '/privacy.html') return;

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  window.gtag('js', new Date());
  var referrerOrigin = '';
  try { if (document.referrer) referrerOrigin = new URL(document.referrer).origin + '/'; } catch (error) {}
  window.gtag('config', measurementId, {
    allow_google_signals: false,
    allow_ad_personalization_signals: false,
    cookie_domain: 'none',
    cookie_expires: 7776000,
    cookie_update: false,
    cookie_flags: 'SameSite=Lax;Secure',
    // Never include URL queries or fragments, which can contain personal data.
    page_location: location.origin + location.pathname,
    page_referrer: referrerOrigin
  });
  var script = document.createElement('script');
  script.async = true;
  script.src = 'https://www.googletagmanager.com/gtag/js?id=' + measurementId;
  document.head.appendChild(script);
}());
