# Kit posted fields

> **Diátaxis:** reference · **Canonical:** `docs/reference/kit-posted-fields.md` · **Layer:** ux-compose

How a live control posts a field, and whether that field arrives on the action.

A rendered control posts every named field of its enclosing form (`args` from `data-channel-args`, `cap` from `data-channel-cap`, `form` from `collectForm`). Fixed names are parameters on the action: `q`, `query`, `text`, `tag`, `code`, `email`, `hex`, `value`. `FilterBar.choose` names `q` too, because the chips sit in the query form; the click applies the chip and keeps the posted query. `Otp.verify` keeps the posted code on the component. `SpinButton.set_value` and `Typeahead.query_hits` already name their fields, and the wire test keeps those markers. FormLayout `set_field` and `submit` take their names from `_fields()`. Login `set_field` writes only the sealed `field`, and `submit` clears the password after a successful sign-in. Those rows wait on `@action(fields=...)`. Do not fold `**kwargs` back in.

`ux-channel.js` `fireControl` sends `data-channel-args` plus the named control (and, for a submit control, the rest of the form). Compose `App.dispatch` receives that payload. ux-behavior `ad86d4c` and compose main's pin `2ae5c3d` both drop a posted key the action signature does not name. A key that is a named parameter arrives. `**kwargs` does not receive the dropped keys. Undeclared keys such as `is_admin` and `role` stay out of the action.

Measured with `App.dispatch` on compose main `c22e419` (ux-behavior `2ae5c3de6c60756cfccfa0174355037436bb3f14`) and on this branch (ux-behavior `ad86d4cc7cf2390f8d1200cdb7d2cc68f6508b82`). The kit source is the same on both. "Arrives" means the component state holds the posted value after that dispatch. Login's successful submit clears the stored password; an empty password error plus `authed` shows the password was accepted. OTP's successful verify keeps the posted code, and `ok` shows the six digits were accepted.

**Static** means the posted names are written in the action. **Dynamic** means the names come from the form (`FormLayout._fields()`), so they are not known as parameters when the action is written.

| Kit | Action | Posted fields | Kind | Main | `ad86d4c` |
|-----|--------|---------------|------|------|-----------|
| FormLayout | `set_field` `components/formlayout.py:131` | names from `_fields()` (default `name`, `email`, `note`) | Dynamic | no | no |
| FormLayout | `submit` `components/formlayout.py:143` | same names | Dynamic | no | no |
| Login | `set_field` `components/login.py:435` | `email`, `password`, `name` | Static | no | no |
| Login | `submit` `components/login.py:458` | `email`, `password`, `name` | Static, already parameters | yes | yes |
| Newsletter | `set_field` `components/newsletter.py:105` | `email` | Static | no | no |
| Newsletter | `subscribe` `components/newsletter.py:114` | `email` | Static, already a parameter | yes | yes |
| Otp | `set_field` `components/otp.py:159` | `code` | Static | no | no |
| Otp | `verify` `components/otp.py:170` | `code` | Static, already a parameter | yes | yes |
| Combobox | `set_field` `components/combobox.py:212` | `q` (also accepts `field="query"`) | Static | no | no |
| Combobox | `type_query` `components/combobox.py:205` | `q` | Static, already a parameter | yes | yes |
| Command | `set_field` `components/command.py:262` | `q` (also accepts `field="query"`) | Static | no | no |
| Command | `type_query` `components/command.py:255` | `q` | Static, already a parameter | yes | yes |
| Chat | `set_field` `components/chat.py:122` | `text` | Static | no | no |
| Chat | `send` `components/chat.py:130` | `text` | Static, already a parameter | yes | yes |
| TagsInput | `set_field` `components/tagsinput.py:103` | `tag` | Static | no | no |
| TagsInput | `add` `components/tagsinput.py:111` | `tag` | Static, already a parameter | yes | yes |
| SearchBar | `set_field` `components/searchbar.py:106` | `q` | Static | no | no |
| SearchBar | `search` `components/searchbar.py:114` | `q` | Static, already a parameter | yes | yes |
| FilterBar | `set_field` `components/filterbar.py:178` | `q` | Static | no | no |
| SpinButton | `set_value` `components/spinbutton.py:127` | `value` | Static, already a parameter | yes | yes |
| ColorPicker | `set_field` `components/colorpicker.py:122` | `hex` | Static | no | no |

FormLayout is the dynamic case. Its field list is the `fields` seam (`_fields()` at `components/formlayout.py:77`). No compose change in this round declares those names. A later allowlist can pass only fields that form declares.

The Main and `ad86d4c` columns are that measurement, taken before any signature change. The static `set_field` rows were the lost posts: the control's name was not a parameter, so the value was stored as `''`. This branch now declares those names on `set_field`, and the same dispatch stores the value. FormLayout is unchanged. SpinButton, and the submit actions that already named their fields, were already yes on both pins.
