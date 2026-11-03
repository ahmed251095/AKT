import { patch } from "@web/core/utils/patch";
import { Editor } from "@html_editor/editor";

/**
 * `Editor.startPlugins()` sets every plugin up in dependency order, and
 * `Editor.destroy()` tears them down in reverse:
 *
 *     while ((plugin = this.plugins.pop())) {
 *         plugin.destroy();          // <- not guarded
 *     }
 *
 * Neither loop survives one bad plugin. If a `setup()` throws, every plugin
 * after it keeps the state it never created - `undefined`. Those same plugins
 * are the first ones popped on teardown, and several of them dereference that
 * state blindly (`this.intersectionObserver.disconnect()` in MoveNodePlugin,
 * `this.resizeObserver` in PositionPlugin, `this.localOverlays` in
 * LocalOverlayPlugin, `this.debouncedUpdateToolbar` in ToolbarPlugin). The
 * second throw aborts the teardown, so the plugins at the *bottom* of the
 * stack are never cleaned up - and SelectionPlugin sits near the bottom,
 * holding a listener on the **document**:
 *
 *     addGlobalDomListener("selectionchange", () => this.updateActiveSelection())
 *
 * That listener outlives its editor for the rest of the page's life. Every
 * later selection change anywhere in the web client - clicking a menu item,
 * typing in a search box - runs the dead editor's handlers, and AlignPlugin
 * (also never set up) throws on each one:
 *
 *     TypeError: Cannot set properties of undefined (setting 'displayName')
 *         at AlignPlugin.updateAlignmentParams
 *
 * which Owl turns into a full-screen "حدث خطأ ما" dialog on a screen that has
 * no editor on it at all. The user gets it again and again until they reload.
 *
 * Draining the plugins with each teardown isolated means the loop always
 * reaches the bottom of the stack, so the document listener always goes away.
 * The first error - the real one - still surfaces; the aftershocks do not.
 */
patch(Editor.prototype, {
    /**
     * Name the plugin whose setup failed. Without this the console only shows
     * the inner error, and the thing it breaks shows up minutes later and
     * somewhere else entirely.
     */
    startPlugins() {
        for (const plugin of this.plugins) {
            const setup = plugin.setup.bind(plugin);
            plugin.setup = () => {
                try {
                    setup();
                } catch (error) {
                    console.error(
                        `[akt] html_editor plugin "${plugin.constructor.id}" crashed during setup`,
                        error
                    );
                    throw error;
                }
            };
        }
        return super.startPlugins();
    },

    destroy(willBeRemoved) {
        let plugin;
        while (this.editable && (plugin = this.plugins.pop())) {
            try {
                plugin.destroy();
            } catch (error) {
                // Report it, but keep going: what is left to tear down is the
                // part that leaks document-level listeners.
                console.error(
                    `[akt] html_editor plugin "${plugin.constructor.id}" crashed during teardown`,
                    error
                );
            }
        }
        // `this.plugins` is empty now, so super's own loop is a no-op; it still
        // does the rest of the teardown (shared, contenteditable, classes).
        return super.destroy(willBeRemoved);
    },
});
