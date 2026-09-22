/* Niya Solutions — site behaviour (vanilla JS, no dependencies). */
(function () {
  'use strict';

  var FORM_ENDPOINT = 'https://formsubmit.co/ajax/info@niya-solutions.be';
  var GTM_ID = 'GTM-PPX774R9';

  var $ = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };
  var desktop = window.matchMedia('(min-width: 1024px)');

  /* ---------- Lazy images (data-src) ---------- */
  function loadImage(el) {
    var src = el.getAttribute('data-src');
    if (!src) return;
    if (el.classList.contains('background_image')) {
      el.style.backgroundImage = "url('" + src + "')";
    } else if (!el.getAttribute('src')) {
      el.setAttribute('src', src);
    }
    el.classList.add('loaded');
  }
  function initLazy() {
    var els = $$('[data-src]');
    if (!('IntersectionObserver' in window)) { els.forEach(loadImage); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { loadImage(e.target); io.unobserve(e.target); }
      });
    }, { rootMargin: '400px 1000px 400px 1000px' });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ---------- Reveal on scroll ---------- */
  function checkReveal() {
    $$('.reveal:not(.show)').forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.bottom >= 0 && r.top <= window.innerHeight) {
        el.classList.add('show');
        setTimeout(function () { el.classList.add('no_trans'); }, 600);
      }
    });
  }

  /* ---------- Mobile navigation ---------- */
  var lockedScrollTop = 0;
  function setNavOpen(open) {
    var menu = $('.header__toggled__menu');
    if (!menu) return;
    menu.classList.toggle('navigation-mobile-open', open);
    document.documentElement.classList.toggle('fiji-nav-open', open);
    document.body.classList.toggle('fiji-nav-open', open);
    $$("[data-action='toggle_nav']").forEach(function (b) {
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
      b.setAttribute('data-state', open ? 'open' : 'closed');
    });
    var bs = document.body.style;
    if (open) {
      lockedScrollTop = window.pageYOffset || document.documentElement.scrollTop || 0;
      bs.position = 'fixed'; bs.top = -lockedScrollTop + 'px'; bs.left = '0'; bs.right = '0'; bs.width = '100%';
    } else {
      bs.position = bs.top = bs.left = bs.right = bs.width = '';
      window.scrollTo(0, lockedScrollTop);
    }
  }
  function initNav() {
    $$("[data-action='toggle_nav']").forEach(function (b) {
      b.addEventListener('click', function (e) {
        e.preventDefault();
        setNavOpen(!$('.header__toggled__menu').classList.contains('navigation-mobile-open'));
      });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        closeAllDropdowns();
        if ($('.header__toggled__menu.navigation-mobile-open')) setNavOpen(false);
      }
    });
    var t;
    window.addEventListener('resize', function () {
      clearTimeout(t);
      t = setTimeout(function () {
        var toggle = $(".navigation-toggle[data-action='toggle_nav']");
        if ($('.header__toggled__menu.navigation-mobile-open') && toggle && getComputedStyle(toggle).display === 'none') setNavOpen(false);
      }, 100);
    });
  }

  /* ---------- Dropdowns ---------- */
  function setDropdown(c, open) {
    var d = $('.menu__dropdown', c), t = $('.menu-tekst', c);
    c.classList.toggle('dropdown-open', open);
    if (d) { d.classList.toggle('nav__mobile--show', open); d.classList.toggle('nav__mobile--hide', !open); }
    if (t) t.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  function closeAllDropdowns(except) {
    $$('.menu__dropdown--container').forEach(function (c) { if (c !== except) setDropdown(c, false); });
  }
  function initDropdowns() {
    var containers = $$('.menu__dropdown--container');
    containers.forEach(function (c) {
      var hi = c.closest('.header__items'); if (hi) hi.classList.add('nav__dropdown');
      var nl = c.closest('.nav__links'); if (nl) nl.classList.add('pillar__submenu');
      var t = $('.menu-tekst', c); if (t) t.removeAttribute('title');
    });
    // Desktop: hover / focus in header
    $$('.header .menu__dropdown--container').forEach(function (c) {
      var timer;
      var open = function () { if (!desktop.matches) return; clearTimeout(timer); closeAllDropdowns(c); c.classList.add('dropdown-open'); };
      var close = function () { if (!desktop.matches) return; clearTimeout(timer); timer = setTimeout(function () { c.classList.remove('dropdown-open'); }, 220); };
      c.addEventListener('mouseenter', open); c.addEventListener('focusin', open);
      c.addEventListener('mouseleave', close); c.addEventListener('focusout', close);
    });
    // Click / tap toggles (mobile menu and keyboard)
    containers.forEach(function (c) {
      c.addEventListener('click', function (e) {
        if (e.target.closest('.menu__dropdown__link')) return;
        e.preventDefault(); e.stopPropagation();
        if (desktop.matches && c.closest('.header')) { closeAllDropdowns(c); setDropdown(c, true); return; }
        var open = !c.classList.contains('dropdown-open');
        closeAllDropdowns(c); setDropdown(c, open);
      });
      var t = $('.menu-tekst', c);
      if (t) t.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); c.click(); }
      });
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.menu__dropdown--container')) closeAllDropdowns();
    });
  }

  /* ---------- Home: service cards (mobile toggle) ---------- */
  function initTeamToggles() {
    $$('.toggle-btn-team').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var details = btn.parentElement.nextElementSibling;
        var expanded = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', String(!expanded));
        btn.style.transform = expanded ? 'rotate(0deg)' : 'rotate(180deg)';
        if (details) details.style.display = expanded ? 'none' : 'grid';
      });
    });
  }

  /* ---------- Home: sticky section title (desktop) ---------- */
  function initTeamTitle() {
    var wrappers = $$('.index__part--team .index__team__wrapper');
    if (!wrappers.length) return;
    var raf = 0;
    function reset(el) {
      el.classList.remove('team-title-is-fixed');
      if (el.__orig) el.setAttribute('style', el.__orig); else el.removeAttribute('style');
    }
    function spacer(w, h) {
      var s = w.__spacer;
      if (!s) {
        s = document.createElement('div'); s.className = 'team-title-spacer';
        var team = $('.index__team', w);
        if (team) team.insertBefore(s, $('.pillars__title__wrapper', w));
        w.__spacer = s;
      }
      s.style.height = h + 'px';
    }
    function unspacer(w) { if (w.__spacer) { w.__spacer.remove(); w.__spacer = null; } }
    function update() {
      raf = 0;
      var offset = window.innerWidth < 768 ? 50 : 120;
      wrappers.forEach(function (w) {
        var title = $('.pillars__title__wrapper', w), team = $('.index__team', w);
        if (!title || !team) return;
        if (title.__orig === undefined) title.__orig = title.getAttribute('style') || '';
        if (!desktop.matches) { unspacer(w); reset(title); return; }
        var wr = w.getBoundingClientRect(), tr = title.getBoundingClientRect(), h = tr.height;
        if (wr.top <= offset && wr.bottom > offset + h) {
          spacer(w, h); title.classList.add('team-title-is-fixed');
          Object.assign(title.style, { position: 'fixed', top: offset + 'px', left: tr.left + 'px', width: tr.width + 'px', zIndex: '60', background: '' });
        } else if (wr.bottom <= offset + h) {
          spacer(w, h); title.classList.remove('team-title-is-fixed');
          Object.assign(title.style, { position: 'absolute', top: Math.max(0, team.offsetHeight - h) + 'px', left: '', width: '', zIndex: '1', background: '' });
        } else { unspacer(w); reset(title); }
      });
    }
    var schedule = function () { if (!raf) raf = requestAnimationFrame(update); };
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    update();
  }

  /* ---------- Home: spacing under hero pillars ---------- */
  function initIndexPadding() {
    var pillars = $('.index-top-pillars'),
        first = $('.page__index > .padding__boxes > .padding__box:first-child'),
        page = $('.page__index');
    if (!pillars || !first || !page) return;
    var mq = window.matchMedia('(max-width: 800px)');
    function update() {
      if (mq.matches) { first.style.removeProperty('--index-description-padding-top'); return; }
      var rem = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
      var v = Math.max(4 * rem, pillars.getBoundingClientRect().bottom - page.getBoundingClientRect().top + 2 * rem);
      first.style.setProperty('--index-description-padding-top', v + 'px');
    }
    update();
    window.addEventListener('load', update);
    window.addEventListener('resize', update);
  }

  /* ---------- Back to top ---------- */
  function initBackToTop() {
    var btn = $('#back_to_top_btn');
    if (!btn) return;
    function check() {
      var nearBottom = window.pageYOffset + window.innerHeight > document.documentElement.scrollHeight - 300;
      btn.classList.toggle('show', nearBottom);
    }
    check();
    window.addEventListener('scroll', check, { passive: true });
    btn.addEventListener('click', function (e) { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); });
  }

  /* ---------- FAQ accordion + search ---------- */
  function slide(el, open) {
    if (open) {
      el.style.display = 'block';
      var h = el.scrollHeight;
      el.style.overflow = 'hidden'; el.style.height = '0px'; el.style.transition = 'height .3s ease';
      requestAnimationFrame(function () { el.style.height = h + 'px'; });
      setTimeout(function () { el.style.height = el.style.overflow = el.style.transition = ''; }, 320);
    } else {
      el.style.overflow = 'hidden'; el.style.height = el.scrollHeight + 'px'; el.style.transition = 'height .3s ease';
      requestAnimationFrame(function () { el.style.height = '0px'; });
      setTimeout(function () { el.style.display = 'none'; el.style.height = el.style.overflow = el.style.transition = ''; }, 320);
    }
  }
  function initFaq() {
    var qs = $$('.faq_question:not([data-notoggle])');
    if (!qs.length) return;
    qs.forEach(function (q) {
      var a = q.nextElementSibling;
      if (a) a.style.display = 'none';
      q.addEventListener('click', function () {
        if (!a) return;
        var open = a.style.display === 'none';
        slide(a, open);
        var part = q.closest('.faq_part'); if (part) part.classList.toggle('active');
        if (q.getAttribute('data-alias')) history.replaceState(null, '', '#' + q.getAttribute('data-alias'));
      });
    });
    var hash = location.hash.slice(1);
    if (hash) {
      var q = $("[data-alias='" + hash.replace(/'/g, '') + "']");
      if (q && q.nextElementSibling) {
        q.nextElementSibling.style.display = 'block';
        var part = q.closest('.faq_part'); if (part) part.classList.add('active');
        setTimeout(function () { window.scrollTo({ top: q.getBoundingClientRect().top + window.pageYOffset - 100, behavior: 'smooth' }); }, 100);
      }
    }
    $$('.faq-category').forEach(function (c) {
      var prev = c.previousElementSibling;
      if (prev && prev.classList.contains('faq-item')) c.style.paddingTop = '15px';
    });
    var field = $('#search_field');
    if (field) field.addEventListener('keyup', function () {
      var v = field.value.toLowerCase(), any = false;
      var noRes = $('#faq_search-noresult');
      $$('.answer_item').forEach(function (item) {
        var q = $('.faq_question', item), t = $("[itemprop='text']", item);
        var hit = !v || (q && q.textContent.toLowerCase().indexOf(v) > -1) || (t && t.textContent.toLowerCase().indexOf(v) > -1);
        item.style.display = hit ? '' : 'none';
        if (hit) any = true;
      });
      $$('.page_text_i').forEach(function (p) { p.style.display = v ? 'none' : ''; });
      if (noRes) noRes.style.display = v && !any ? '' : 'none';
    });
  }

  /* ---------- Horizontal category scroller (FAQ) ---------- */
  function initCategoryScroller() {
    $$('.categories-slider').forEach(function (s) {
      var box = s.closest('.faq__categories-container, .menu__categories-container, .tag__categories-container');
      if (!box) return;
      var l = $('.arrow-scroller.left', box), r = $('.arrow-scroller.right', box);
      if (!l || !r) return;
      box.style.position = 'relative';
      function upd() {
        var max = s.scrollWidth - s.clientWidth;
        l.style.display = max > 1 && s.scrollLeft > 1 ? 'flex' : 'none';
        r.style.display = max > 1 && s.scrollLeft < max - 1 ? 'flex' : 'none';
      }
      l.addEventListener('click', function () { s.scrollBy({ left: -200, behavior: 'smooth' }); });
      r.addEventListener('click', function () { s.scrollBy({ left: 200, behavior: 'smooth' }); });
      s.addEventListener('scroll', upd); window.addEventListener('resize', upd);
      requestAnimationFrame(upd);
    });
  }

  /* ---------- Sticky header shadow ---------- */
  function initStickyHeader() {
    var h = $('.header.sticky-nav');
    if (!h) return;
    window.addEventListener('scroll', function () {
      h.classList.toggle('scrolled', window.scrollY > (window.innerWidth < 768 ? 50 : 100));
    }, { passive: true });
  }

  /* ---------- Search forms (site search) ---------- */
  function initSearchForms() {
    $$('.search_form').forEach(function (f) {
      f.addEventListener('submit', function (e) {
        var input = $('.search_form_input', f);
        if (input && !input.value.trim()) e.preventDefault();
      });
    });
  }

  /* ---------- Search page ---------- */
  function initSearchPage() {
    var list = $('#page_search_i');
    if (!list) return;
    var input = $('#keyword'), noResult = $('#search_noresult'), form = $('#searchForm');
    var keyword = (new URLSearchParams(location.search).get('keyword') || '').trim();
    input.value = keyword;
    var reset = $('button[type=reset]', form);
    if (reset) reset.addEventListener('click', function (e) {
      e.preventDefault(); input.value = ''; list.innerHTML = ''; noResult.style.display = 'none';
      history.replaceState(null, '', location.pathname);
    });
    if (!keyword) return;
    var root = list.getAttribute('data-search-index').replace(/assets\/search-index\.json$/, '');
    var fold = function (s) { return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); };
    var words = fold(keyword).split(/\s+/).filter(Boolean);
    fetch(list.getAttribute('data-search-index')).then(function (r) { return r.json(); }).then(function (items) {
      var hits = [];
      items.forEach(function (it) {
        var all = fold(it.t) + ' ' + fold(it.d) + ' ' + fold(it.x);
        if (!words.every(function (w) { return all.indexOf(w) > -1; })) return;
        hits.push({ it: it });
      });
      list.innerHTML = hits.map(function (h) {
        var name = h.it.t.replace(/\s*\|\s*Niya Solutions$/, '');
        var a = document.createElement('a');
        a.href = root + h.it.u; a.className = 'page_search_item';
        var h5 = document.createElement('h5'); h5.textContent = name; a.appendChild(h5);
        return '<div>' + a.outerHTML + '</div>';
      }).join('');
      noResult.style.display = hits.length ? 'none' : '';
    });
  }

  /* ---------- Forms ---------- */
  function initForms() {
    $$('form[data-niya-form]').forEach(function (form) {
      var box = form.closest('[data-part="event"]');
      var errors = $('.error-ul', form);
      var busy = false;
      function showError(msg) {
        errors.innerHTML = '<li>' + msg + '</li>';
        errors.style.display = '';
        scrollToBox();
      }
      function scrollToBox() {
        window.scrollTo({ top: box.getBoundingClientRect().top + window.pageYOffset - 100, behavior: 'smooth' });
      }
      form.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') e.preventDefault();
      });
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        if (busy) return;
        errors.style.display = 'none';
        var data = { _subject: form.getAttribute('data-subject') || 'Nieuw bericht via niya-solutions.be', _template: 'table', _captcha: 'false' };
        var missing = null;
        $$('[data-question]', form).forEach(function (field) {
          var label = field.getAttribute('data-question');
          var required = field.hasAttribute('data-required');
          var value;
          if (field.classList.contains('checks')) {
            var checked = $$('input:checked', field).map(function (i) { return i.value; });
            value = checked.join(', ');
          } else if (field.tagName === 'SELECT') {
            value = field.selectedIndex > 0 ? field.value : '';
          } else {
            value = field.value.trim();
          }
          if (required && !value && !missing) missing = label;
          data[label] = value;
        });
        var email = $('input[data-email]', form);
        if (missing) return showError('Het veld ' + missing.toLowerCase() + ' is verplicht.');
        if (email && email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) return showError('Het e-mailadres is ongeldig.');
        if (!$('input[name="gdpr"]', form).checked) return showError('Je moet akkoord gaan met de privacy en algemene voorwaarden.');
        if ($('input[name="contact_me_by_fax_only"]', form).checked) return; // honeypot
        if (email) data._replyto = email.value.trim();
        data.Pagina = location.href;
        busy = true;
        form.classList.add('is-sending');
        fetch(FORM_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify(data)
        }).then(function (r) {
          if (!r.ok) throw new Error(r.status);
          return r.json();
        }).then(function () {
          var done = document.createElement('div');
          done.id = 'event_form_submitted';
          done.className = 'event_form_message';
          done.innerHTML = form.getAttribute('data-success');
          form.parentNode.replaceChild(done, form);
          scrollToBox();
          if (window.dataLayer) window.dataLayer.push({ event: 'formSubmission', formType: form.getAttribute('data-name') });
        }).catch(function () {
          busy = false;
          form.classList.remove('is-sending');
          showError('Oeps, er is iets foutgelopen. Probeer later opnieuw.');
        });
      });
    });
  }

  /* ---------- Cookie consent + Google Tag Manager ---------- */
  function getCookie(name) {
    var m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }
  function setCookie(name, value) {
    var d = new Date(); d.setTime(d.getTime() + 100 * 24 * 60 * 60 * 1000);
    document.cookie = name + '=' + value + ';expires=' + d.toUTCString() + ';path=/;SameSite=Lax';
  }
  function loadGtm() {
    if (!GTM_ID || window.__gtmLoaded) return;
    window.__gtmLoaded = true;
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
    var s = document.createElement('script');
    s.async = true; s.src = 'https://www.googletagmanager.com/gtm.js?id=' + GTM_ID;
    document.head.appendChild(s);
  }
  function initCookies() {
    var popup = $('[data-cookie-popup]');
    var consent = getCookie('CookieConsent');
    if (consent === 'true') loadGtm();
    if (!popup) return;
    if (consent === '') popup.style.display = 'block';
    function hide() { slide(popup, false); }
    $$('[data-cookie-accept-all]', popup).forEach(function (b) {
      b.addEventListener('click', function (e) { e.preventDefault(); setCookie('CookieConsent', 'true'); loadGtm(); hide(); });
    });
    $$('[data-cookie-edit]', popup).forEach(function (b) {
      b.addEventListener('click', function (e) {
        e.preventDefault();
        var opts = $('[data-cookie-options]', popup);
        slide(opts, getComputedStyle(opts).display === 'none');
      });
    });
    $$('[data-cookie-save]', popup).forEach(function (b) {
      b.addEventListener('click', function (e) {
        e.preventDefault();
        var track = $('[data-cookie-tracking-check]', popup).checked;
        setCookie('CookieConsent', track ? 'true' : 'false');
        if (track) loadGtm();
        hide();
      });
    });
  }

  /* ---------- Empty links ---------- */
  function initEmptyLinks() {
    $$('.link-img[href=""], .link[href=""], .partners__link[href=""]').forEach(function (a) {
      a.addEventListener('click', function (e) { e.preventDefault(); });
    });
  }

  function init() {
    initLazy();
    initNav();
    initDropdowns();
    initTeamToggles();
    initTeamTitle();
    initIndexPadding();
    initBackToTop();
    initFaq();
    initCategoryScroller();
    initStickyHeader();
    initSearchForms();
    initSearchPage();
    initForms();
    initCookies();
    initEmptyLinks();
    checkReveal();
    window.addEventListener('scroll', checkReveal, { passive: true });
    window.addEventListener('resize', checkReveal);
    window.addEventListener('load', function () { document.body.classList.add('body__loaded'); checkReveal(); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
