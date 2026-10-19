# sourced by tests/test.sh: unit programs
for t in t_app t_ext t_foldstart t_buffer t_frecency t_fuzzy t_git t_grep t_ignore t_key t_keymap t_lsp t_map t_picker t_projconf t_register t_session t_snippet t_sources t_surround t_syntax t_text t_theme t_tree t_undofile t_vt t_window t_wrapmap; do
    unit "$t"
done
