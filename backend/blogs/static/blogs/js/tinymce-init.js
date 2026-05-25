document.addEventListener('DOMContentLoaded', function () {
  if (typeof tinymce === 'undefined') return;

  tinymce.init({
    selector: 'textarea.rich-text-editor',
    menubar: false,
    plugins: 'autolink lists link charmap preview',
    toolbar: 'undo redo | bold italic underline | fontsizeselect forecolor backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | preview',
    toolbar_mode: 'wrap',
    branding: false,
    element_format: 'html',
    forced_root_block: 'p',
    content_style: 'body { font-family: system-ui, sans-serif; font-size: 16px; }',
  });
});
