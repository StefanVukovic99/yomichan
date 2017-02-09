/*
 * Copyright (C) 2016  Alex Yatskov <alex@foosoft.net>
 * Author: Alex Yatskov <alex@foosoft.net>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

class Frame {
    constructor() {
        this.definitions = [];
        this.audioCache = {};
        this.sequence = 0;

        $(window).on('message', e => {
            const {action, params} = e.originalEvent.data, method = this['api_' + action];
            if (typeof(method) === 'function') {
                method.call(this, params);
            }
        });
    }

    api_showTermDefs({definitions, options}) {
        const sequence = ++this.sequence;
        const context = {
            definitions,
            grouped: options.general.groupResults,
            addable: options.ankiMethod !== 'disabled',
            playback: options.general.audioPlayback
        };

        this.definitions = definitions;
        this.showSpinner(false);
        window.scrollTo(0, 0);

        renderText(context, 'terms.html').then(content => {
            $('#content').html(content);
            $('.action-add-note').click(this.onAddNote.bind(this));

            $('.kanji-link').click(e => {
                e.preventDefault();
                const character = $(e.target).text();
                findKanji(character).then(kdefs => {
                    kdefs.forEach(kdef => {
                        kdef.url = definitions[0].url;
                        kdef.sentence = definitions[0].sentence;
                    });

                    this.api_showKanjiDefs({options, definitions: kdefs});
                });
            });

            $('.action-play-audio').click(e => {
                e.preventDefault();
                const index = $(e.currentTarget).data('index');
                this.playAudio(this.definitions[index]);
            });

            this.updateAddNoteButtons(['term_kanji', 'term_kana'], sequence);
        }).catch(error => {
            this.handleError(error);
        });
    }

    api_showKanjiDefs({definitions, options}) {
        const sequence = ++this.sequence;
        const context = {
            definitions,
            addable: options.ankiMethod !== 'disabled'
        };

        this.definitions = definitions;
        this.showSpinner(false);
        window.scrollTo(0, 0);

        renderText(context, 'kanji.html').then(content => {
            $('#content').html(content);
            $('.action-add-note').click(this.onAddNote.bind(this));

            this.updateAddNoteButtons(['kanji'], sequence);
        }).catch(error => {
            this.handleError(error);
        });
    }

    api_showOrphaned() {
        $('#content').hide();
        $('#orphan').show();
    }

    findAddNoteButton(index, mode) {
        return $(`.action-add-note[data-index="${index}"][data-mode="${mode}"]`);
    }

    onAddNote(e) {
        e.preventDefault();
        this.showSpinner(true);

        const link = $(e.currentTarget);
        const index = link.data('index');
        const mode = link.data('mode');

        addDefinition(this.definitions[index], mode).then(success => {
            if (success) {
                const button = this.findAddNoteButton(index, mode);
                button.addClass('disabled');
            } else {
                showError('note could not be added');
            }
        }).catch(error => {
            this.handleError(error);
        }).then(() => {
            this.showSpinner(false);
        });
    }

    updateAddNoteButtons(modes, sequence) {
        canAddDefinitions(this.definitions, modes).then(states => {
            if (states === null) {
                return;
            }

            if (sequence !== this.sequence) {
                return;
            }

            states.forEach((state, index) => {
                for (const mode in state) {
                    const button = this.findAddNoteButton(index, mode);
                    if (state[mode]) {
                        button.removeClass('disabled');
                    } else {
                        button.addClass('disabled');
                    }

                    button.removeClass('pending');
                }
            });
        }).catch(error => {
            this.handleError(error);
        });
    }

    showSpinner(show) {
        const spinner = $('.spinner');
        if (show) {
            spinner.show();
        } else {
            spinner.hide();
        }
    }

    playAudio(definition) {
        let url = `https://assets.languagepod101.com/dictionary/japanese/audiomp3.php?kanji=${encodeURIComponent(definition.expression)}`;
        if (definition.reading) {
            url += `&kana=${encodeURIComponent(definition.reading)}`;
        }

        for (const key in this.audioCache) {
            this.audioCache[key].pause();
        }

        const audio = this.audioCache[url] || new Audio(url);
        audio.currentTime = 0;
        audio.play();
    }

    handleError(error) {
        if (window.orphaned) {
            this.api_showOrphaned();
        } else {
            showError(error);
        }
    }
}

window.frame = new Frame();
