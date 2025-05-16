document.addEventListener('DOMContentLoaded', () => {
  const wrappers = document.querySelectorAll('.image-wrapper');
  const hiddenInput = document.getElementById('selected-image-id');

  wrappers.forEach(wrapper => {
    wrapper.addEventListener('click', () => {
      wrappers.forEach(w => w.classList.remove('selected'));
      wrapper.classList.add('selected');
      const imgId = wrapper.querySelector('img').dataset.imgId;
      hiddenInput.value = imgId;
    });
  });

});
