# Kit posted fields

> **Diátaxis:** reference · **Canonical:** `docs/reference/kit-posted-fields.md` · **Layer:** ux-compose

How a live control posts a field, and whether that field arrives on the action.

A rendered control posts every named field of its enclosing form (`args` from `data-channel-args`, `cap` from `data-channel-cap`, `form` from `collectForm`). Kit `set_field` matches main `c22e419`: the control's name is not a parameter, `**kwargs` does not receive it, and the value is not stored. There is one instance per component id and one shared store, so storing that value and painting it would show one visitor's input on the next visitor's page. Restoring kit fields waits on a per-visitor state decision. This does not start `@action(fields=...)` work.

`FilterBar.choose` names `q` and ignores it. The chips sit in the query form, so the click has to accept `q` or the action does not run. The query is not written. `Otp.verify` checks the posted code and then clears it. A password and an OTP code are not painted back into the page. PasswordField's lede is eight bullets when a secret is stored, and `empty` when it is not. Actions that already named their field on main (`submit`, `send`, `type_query`, `search`, `add`, `set_value`, `query_hits`) still store it. Isolating those waits on the same per-visitor decision.

A named signature rejects an extra posted key, such as a host `csrf` field. That is a validation error: the action does not run. This strict behaviour stays. `**kwargs` does not receive that key either. FormLayout still runs, and its dynamic names are not stored.

`ux-channel.js` `fireControl` sends `data-channel-args` plus the named control (and, for a submit control, the rest of the form). Compose `App.dispatch` receives that payload. A key that is a named parameter arrives. Undeclared keys such as `is_admin` and `role` are the same validation error.

Measured with `App.dispatch` on compose main `c22e419` (ux-behavior `2ae5c3de6c60756cfccfa0174355037436bb3f14`) and on this branch (ux-behavior `09a9a658e7dbd06f51acf6104a85c3ba608dfe7a`). Kit `set_field` matches main. `FilterBar.choose` is the exception: it names `q` and does not store it. "Arrives" means the component state holds the posted value after that dispatch. Login's successful submit clears the stored password; an empty password error plus `authed` shows the password was accepted. OTP's successful verify clears the posted code, and `ok` shows the six digits were accepted. A password, an OTP code, and PasswordField's secret are not painted. The PasswordField lede is eight bullets when a secret is stored, and `empty` when it is not.

**Static** means the posted names are written in the action. **Dynamic** means the names come from the form (`FormLayout._fields()`), so they are not known as parameters when the action is written.

| Kit | Action | Posted fields | Kind | Main | `09a9a65` |
|-----|--------|---------------|------|------|-----------|
| FormLayout | `set_field` `components/formlayout.py:131` | names from `_fields()` (default `name`, `email`, `note`) | Dynamic | no | no |
| FormLayout | `submit` `components/formlayout.py:143` | same names | Dynamic | no | no |
| Login | `set_field` `components/login.py:435` | `email`, `password`, `name` | Static | no | no |
| Login | `submit` `components/login.py:450` | `email`, `password`, `name` | Static, already parameters | yes | yes |
| Newsletter | `set_field` `components/newsletter.py:105` | `email` | Static | no | no |
| Newsletter | `subscribe` `components/newsletter.py:113` | `email` | Static, already a parameter | yes | yes |
| Otp | `set_field` `components/otp.py:158` | `code` | Static | no | no |
| Otp | `verify` `components/otp.py:168` | `code` | Static, already a parameter | yes | yes |
| Combobox | `set_field` `components/combobox.py:212` | `q` (also accepts `field="query"`) | Static | no | no |
| Combobox | `type_query` `components/combobox.py:205` | `q` | Static, already a parameter | yes | yes |
| Command | `set_field` `components/command.py:262` | `q` (also accepts `field="query"`) | Static | no | no |
| Command | `type_query` `components/command.py:255` | `q` | Static, already a parameter | yes | yes |
| Chat | `set_field` `components/chat.py:122` | `text` | Static | no | no |
| Chat | `send` `components/chat.py:129` | `text` | Static, already a parameter | yes | yes |
| TagsInput | `set_field` `components/tagsinput.py:103` | `tag` | Static | no | no |
| TagsInput | `add` `components/tagsinput.py:110` | `tag` | Static, already a parameter | yes | yes |
| SearchBar | `set_field` `components/searchbar.py:106` | `q` | Static | no | no |
| SearchBar | `search` `components/searchbar.py:113` | `q` | Static, already a parameter | yes | yes |
| FilterBar | `set_field` `components/filterbar.py:178` | `q` | Static | no | no |
| FilterBar | `choose` `components/filterbar.py:185` | `q` (named so the chip click runs; not stored) | Static | no `q` parameter | no |
| SpinButton | `set_value` `components/spinbutton.py:127` | `value` | Static, already a parameter | yes | yes |
| ColorPicker | `set_field` `components/colorpicker.py:122` | `hex` | Static | no | no |

FormLayout is the dynamic case. Its field list is the `fields` seam (`_fields()` at `components/formlayout.py:77`). Those names are not parameters, so they are not stored. Restoring them waits on a per-visitor state decision.

The Main and `09a9a65` columns are whether the posted name is in component state after dispatch. The static `set_field` rows are no on both: the control's name is not a parameter. This branch matches that. It does not declare those names. Login `submit` still clears the password. SpinButton, and the other actions that already named their fields, were already yes on both.
