// script.js — behaviour for MentalHealth auth page

// Wrap everything in DOMContentLoaded for safety
window.addEventListener('DOMContentLoaded', ()=>{
  // Toggle panels
  const btnLogin = document.getElementById('btn-login');
  const btnSignup = document.getElementById('btn-signup');
  const loginPanel = document.getElementById('login-panel');
  const signupPanel = document.getElementById('signup-panel');

  function showLogin(){
    btnLogin.classList.add('active');btnLogin.setAttribute('aria-selected','true');
    btnSignup.classList.remove('active');btnSignup.setAttribute('aria-selected','false');
    loginPanel.style.display='block';signupPanel.style.display='none';
  }
  function showSignup(){
    btnSignup.classList.add('active');btnSignup.setAttribute('aria-selected','true');
    btnLogin.classList.remove('active');btnLogin.setAttribute('aria-selected','false');
    loginPanel.style.display='none';signupPanel.style.display='block';
  }

  btnLogin.addEventListener('click', showLogin);
  btnSignup.addEventListener('click', showSignup);

  // Password toggle
  function makeToggle(idInput, idToggle){
    const inp = document.getElementById(idInput);
    const tgl = document.getElementById(idToggle);
    if(!inp || !tgl) return;
    tgl.addEventListener('click', ()=>{
      if(inp.type === 'password') { inp.type = 'text'; tgl.textContent = '🙈'; tgl.title='Hide password' }
      else { inp.type = 'password'; tgl.textContent = '👁️'; tgl.title='Show password' }
    })
  }
  makeToggle('login-pass','toggle-pass');
  makeToggle('signup-pass','toggle-pass-2');

  // Simple client-side validation and demo submit handlers
  const loginForm = document.getElementById('login-form');
  const signupForm = document.getElementById('signup-form');

  loginForm.addEventListener('submit', (e)=>{
    e.preventDefault();
    const email = document.getElementById('login-email');
    const pass = document.getElementById('login-pass');
    if(!email.value || !pass.value || pass.value.length < 6){
      alert('Please enter a valid email and a password with at least 6 characters.');
      return;
    }
    alert('Welcome back — login successful (demo).');
    loginForm.reset();
  });

  signupForm.addEventListener('submit', (e)=>{
    e.preventDefault();
    const first = document.getElementById('first');
    const last = document.getElementById('last');
    const email = document.getElementById('signup-email');
    const pass = document.getElementById('signup-pass');
    const helper = document.getElementById('signup-helper');

    if(!first.value || !last.value || !email.value || !pass.value || pass.value.length < 6){
      helper.classList.add('show');
      setTimeout(()=>helper.classList.remove('show'),4000);
      return;
    }

    alert('Account created — welcome to MentalHealth (demo).');
    signupForm.reset();
    showLogin();
  });

  document.getElementById('cancel-signup').addEventListener('click', ()=>{
    signupForm.reset();
    showLogin();
  });

  document.getElementById('forgot').addEventListener('click', ()=>{
    const e = document.getElementById('login-email');
    const email = e.value || '';
    alert('If an account exists for "' + email + '", we\'ve sent a password reset link (demo).');
  });

  // Keyboard accessibility
  document.addEventListener('keydown', (ev)=>{
    if(ev.key === 'ArrowLeft' || ev.key === 'ArrowRight'){
      ev.preventDefault();
      if(ev.key === 'ArrowRight') showSignup(); else showLogin();
    }
  });
});
