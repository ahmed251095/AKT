import { patch } from "@web/core/utils/patch";
import { AlignPlugin } from "@html_editor/main/align/align_plugin";

/**
 * Safety net under [editor_teardown_patch.js]: `this.alignment` is created in
 * `setup()`, and `updateAlignmentParams` is wired to `selectionchange`, which
 * is a listener on the document. A plugin that was never set up has no
 * alignment to report - that is not an error worth a full-screen dialog.
 */
patch(AlignPlugin.prototype, {
    updateAlignmentParams() {
        if (!this.alignment || this.isDestroyed) {
            return;
        }
        return super.updateAlignmentParams();
    },
});
