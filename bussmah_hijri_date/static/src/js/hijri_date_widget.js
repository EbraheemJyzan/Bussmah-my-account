import { Component, useState, onWillUpdateProps, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";
import { localization } from "@web/core/l10n/localization";

// -------------------------------------------------------------------------
// Constants and Helpers
// -------------------------------------------------------------------------

const HIJRI_MONTHS = [
    { value: 1, label: "1. محرم (Muharram)" },
    { value: 2, label: "2. صفر (Safar)" },
    { value: 3, label: "3. ربيع الأول (Rabi' I)" },
    { value: 4, label: "4. ربيع الآخر (Rabi' II)" },
    { value: 5, label: "5. جمادى الأولى (Jumada I)" },
    { value: 6, label: "6. جمادى الآخرة (Jumada II)" },
    { value: 7, label: "7. رجب (Rajab)" },
    { value: 8, label: "8. شعبان (Sha'ban)" },
    { value: 9, label: "9. رمضان (Ramadan)" },
    { value: 10, label: "10. شوال (Shawwal)" },
    { value: 11, label: "11. ذو القعدة (Dhu al-Qadah)" },
    { value: 12, label: "12. ذو الحجة (Dhu al-Hijjah)" }
];

const GREGORIAN_MONTHS = [
    { value: 1, label: "1. January (يناير)" },
    { value: 2, label: "2. February (فبراير)" },
    { value: 3, label: "3. March (مارس)" },
    { value: 4, label: "4. April (أبريل)" },
    { value: 5, label: "5. May (مايو)" },
    { value: 6, label: "6. June (يونيو)" },
    { value: 7, label: "7. July (يوليو)" },
    { value: 8, label: "8. August (أغسطس)" },
    { value: 9, label: "9. September (سبتمبر)" },
    { value: 10, label: "10. October (أكتوبر)" },
    { value: 11, label: "11. November (نوفمبر)" },
    { value: 12, label: "12. December (ديسمبر)" }
];

const HIJRI_MONTH_NAMES = [
    "",
    "محرم", "صفر", "ربيع الأول", "ربيع الآخر", "جمادى الأولى", "جمادى الآخرة",
    "رجب", "شعبان", "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
];

// Convert Gregorian Date object to Hijri object { y, m, d }
function gregorianToHijri(date) {
    if (!date) return null;
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) return null;
    
    const formatter = new Intl.DateTimeFormat('en-US-u-ca-islamic-umalqura', {
        day: 'numeric', month: 'numeric', year: 'numeric', timeZone: 'UTC'
    });
    
    const parts = formatter.formatToParts(d);
    let y, m, dayVal;
    for (const p of parts) {
        if (p.type === 'year') y = parseInt(p.value, 10);
        if (p.type === 'month') m = parseInt(p.value, 10);
        if (p.type === 'day') dayVal = parseInt(p.value, 10);
    }
    return { y, m, d: dayVal };
}

// Convert Hijri date to Gregorian Date object (UTC)
function hijriToGregorian(hy, hm, hd) {
    let gy = Math.floor(hy * 0.97 + 621.5);
    let date = new Date(Date.UTC(gy, hm - 1, hd));
    
    const formatter = new Intl.DateTimeFormat('en-US-u-ca-islamic-umalqura', {
        day: 'numeric', month: 'numeric', year: 'numeric', timeZone: 'UTC'
    });

    function getH(d) {
        const parts = formatter.formatToParts(d);
        let y, m, dayVal;
        for (const p of parts) {
            if (p.type === 'year') y = parseInt(p.value, 10);
            if (p.type === 'month') m = parseInt(p.value, 10);
            if (p.type === 'day') dayVal = parseInt(p.value, 10);
        }
        return { y, m, d: dayVal };
    }

    for (let i = 0; i < 20; i++) {
        const h = getH(date);
        if (!h.y || !h.m || !h.d) break;
        if (h.y === hy && h.m === hm && h.d === hd) return date;
        
        const targetDays = hy * 354.367 + (hm - 1) * 29.53 + hd;
        const currentDays = h.y * 354.367 + (h.m - 1) * 29.53 + h.d;
        let diff = Math.round(targetDays - currentDays);
        if (diff === 0) diff = targetDays > currentDays ? 1 : -1;
        date.setUTCDate(date.getUTCDate() + diff);
    }
    return null;
}

// Get number of days in a Hijri month
function getDaysInHijriMonth(year, month) {
    let gDate = hijriToGregorian(year, month, 30);
    if (!gDate) return 29;
    let hDate = gregorianToHijri(gDate);
    return hDate.d === 30 ? 30 : 29;
}

// Get the component order of day, month, and year from standard Odoo configuration
function getDateFormatOrder(formatStr) {
    const cleanFormat = formatStr.toLowerCase();
    const dIdx = cleanFormat.indexOf('d');
    const mIdx = cleanFormat.indexOf('m');
    const yIdx = cleanFormat.indexOf('y');
    
    const positions = [
        { type: 'day', index: dIdx },
        { type: 'month', index: mIdx },
        { type: 'year', index: yIdx }
    ].filter(p => p.index !== -1).sort((a, b) => a.index - b.index);
    
    return positions.map(p => p.type);
}

// Format Hijri Date with settings format
function formatHijriWithFormat(hy, hm, hd, formatStr) {
    let result = formatStr;
    // Replace year (4 digits first, then 2 digits)
    result = result.replace(/yyyy/g, String(hy).padStart(4, '0'));
    result = result.replace(/yy/g, String(hy % 100).padStart(2, '0'));
    
    // Replace month names if present
    const monthName = HIJRI_MONTH_NAMES[hm] || "";
    result = result.replace(/MMMM/g, monthName);
    result = result.replace(/MMM/g, monthName);
    
    // Replace month (2 digits, then 1 digit)
    result = result.replace(/MM/g, String(hm).padStart(2, '0'));
    result = result.replace(/M/g, String(hm));
    
    // Replace day (2 digits, then 1 digit)
    result = result.replace(/dd/g, String(hd).padStart(2, '0'));
    result = result.replace(/d/g, String(hd));
    
    return result;
}

// Generate the display format placeholder for the input field
function getPlaceholderForFormat(formatStr, mode, showTime) {
    let fmt = formatStr.toLowerCase();
    
    if (mode === 'hijri') {
        fmt = fmt.replace(/yyyy/g, 'هـهـهـه')
                 .replace(/yy/g, 'هـهـ')
                 .replace(/mm/g, 'ش ش')
                 .replace(/dd/g, 'ي ي')
                 .replace(/m/g, 'ش')
                 .replace(/d/g, 'ي');
        if (showTime) {
            fmt += " س س:د د";
        }
    } else {
        fmt = fmt.toUpperCase();
        if (showTime) {
            fmt += " HH:MM";
        }
    }
    return fmt;
}

// Parse input string based on display mode and Odoo language configuration
function parseDateString(str, mode) {
    if (!str) return null;
    const cleanStr = str.replace(/[-\/.]/g, '-');
    const parts = cleanStr.trim().split(/\s+/);
    const dateParts = parts[0].split('-');
    if (dateParts.length !== 3) return null;
    
    const formatStr = localization.dateFormat || "yyyy-MM-dd";
    const order = getDateFormatOrder(formatStr);
    
    let year, month, day;
    for (let i = 0; i < 3; i++) {
        const val = parseInt(dateParts[i], 10);
        if (isNaN(val)) return null;
        
        const partType = order[i];
        if (partType === 'year') year = val;
        else if (partType === 'month') month = val;
        else if (partType === 'day') day = val;
    }
    
    if (year === undefined || month === undefined || day === undefined) {
        year = parseInt(dateParts[0], 10);
        month = parseInt(dateParts[1], 10);
        day = parseInt(dateParts[2], 10);
    }
    
    if (isNaN(year) || isNaN(month) || isNaN(day)) return null;
    if (month < 1 || month > 12 || day < 1 || day > 31) return null;
    
    if (year < 100) {
        if (mode === 'hijri') {
            year += 1400;
        } else {
            year += 2000;
        }
    }
    
    let hour = 0, minute = 0;
    if (parts[1]) {
        const timeParts = parts[1].split(':');
        hour = parseInt(timeParts[0], 10) || 0;
        minute = parseInt(timeParts[1], 10) || 0;
    }
    
    if (mode === 'hijri') {
        if (day > 30) return null;
        const gDate = hijriToGregorian(year, month, day);
        if (!gDate) return null;
        gDate.setUTCHours(hour);
        gDate.setUTCMinutes(minute);
        return gDate;
    } else {
        const gDate = new Date(Date.UTC(year, month - 1, day, hour, minute));
        if (isNaN(gDate.getTime())) return null;
        return gDate;
    }
}

// Format Gregorian Date using Odoo localized format
function formatGDate(date, showTime) {
    if (!date) return "";
    const { DateTime } = window.luxon;
    const luxonDate = DateTime.fromJSDate(date, { zone: "utc" });
    const format = showTime 
        ? (localization.dateTimeFormat || "yyyy-MM-dd HH:mm:ss") 
        : (localization.dateFormat || "yyyy-MM-dd");
    return luxonDate.toFormat(format);
}

// Format Hijri Date using Odoo localized format order/separators
function formatHDate(date, showTime) {
    if (!date) return "";
    const h = gregorianToHijri(date);
    if (!h) return "";
    
    const dateFormat = localization.dateFormat || "yyyy-MM-dd";
    let formattedDate = formatHijriWithFormat(h.y, h.m, h.d, dateFormat);
    
    if (showTime) {
        const timeFormat = localization.timeFormat || "HH:mm:ss";
        const { DateTime } = window.luxon;
        const luxonDate = DateTime.fromJSDate(date, { zone: "utc" });
        formattedDate += " " + luxonDate.toFormat(timeFormat);
    }
    return formattedDate;
}

// -------------------------------------------------------------------------
// Component definition
// -------------------------------------------------------------------------

export class HijriDateField extends Component {
    static props = {
        ...standardFieldProps,
        showTime: { type: Boolean, optional: true },
        placeholder: { type: String, optional: true },
        required: { type: Boolean, optional: true },
    };
    
    static defaultProps = {
        showTime: false,
    };
    
    static template = "bussmah_hijri_date.HijriDateField";
    
    setup() {
        this.rootRef = useRef("root");
        
        this.state = useState({
            currentMode: "hijri", // Default mode: Hijri
            showPicker: false,
            pickerYear: 1447,
            pickerMonth: 11,
            pickerHour: 12,
            pickerMinute: 0,
        });
        
        this.initPickerFromValue();
        
        const onDocumentClick = (ev) => {
            if (this.state.showPicker && this.rootRef.el && !this.rootRef.el.contains(ev.target)) {
                this.closePicker();
            }
        };
        
        onMounted(() => {
            document.addEventListener("click", onDocumentClick, true);
        });
        
        onWillUnmount(() => {
            document.removeEventListener("click", onDocumentClick, true);
        });
    }
    
    onWillUpdateProps(nextProps) {
        const currentVal = this.props.record.data[this.props.name];
        const nextVal = nextProps.record.data[nextProps.name];
        if (currentVal !== nextVal) {
            const val = this.getJSDateFromRaw(nextVal);
            if (val) {
                this.state.pickerHour = val.getUTCHours();
                this.state.pickerMinute = val.getUTCMinutes();
                if (this.state.currentMode === "hijri") {
                    const h = gregorianToHijri(val);
                    if (h) {
                        this.state.pickerYear = h.y;
                        this.state.pickerMonth = h.m;
                    }
                } else {
                    this.state.pickerYear = val.getUTCFullYear();
                    this.state.pickerMonth = val.getUTCMonth() + 1;
                }
            }
        }
    }
    
    getJSDateFromRaw(raw) {
        if (!raw) return null;
        if (raw.toJSDate) {
            return new Date(Date.UTC(raw.year, raw.month - 1, raw.day, raw.hour || 0, raw.minute || 0));
        }
        const d = new Date(raw);
        return new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate(), d.getHours(), d.getMinutes()));
    }
    
    initPickerFromValue() {
        const val = this.currentValue;
        if (val) {
            this.state.pickerHour = val.getUTCHours();
            this.state.pickerMinute = val.getUTCMinutes();
            if (this.state.currentMode === "hijri") {
                const h = gregorianToHijri(val);
                if (h) {
                    this.state.pickerYear = h.y;
                    this.state.pickerMonth = h.m;
                }
            } else {
                this.state.pickerYear = val.getUTCFullYear();
                this.state.pickerMonth = val.getUTCMonth() + 1;
            }
        } else {
            const today = new Date();
            this.state.pickerHour = today.getHours();
            this.state.pickerMinute = today.getMinutes();
            if (this.state.currentMode === "hijri") {
                const h = gregorianToHijri(today);
                if (h) {
                    this.state.pickerYear = h.y;
                    this.state.pickerMonth = h.m;
                }
            } else {
                this.state.pickerYear = today.getFullYear();
                this.state.pickerMonth = today.getMonth() + 1;
            }
        }
    }
    
    get currentValue() {
        return this.getJSDateFromRaw(this.props.record.data[this.props.name]);
    }
    
    get formattedGregorianValue() {
        return formatGDate(this.currentValue, this.props.showTime);
    }
    
    get formattedHijriValue() {
        return formatHDate(this.currentValue, this.props.showTime);
    }
    
    get inputValue() {
        if (!this.currentValue) return "";
        return this.state.currentMode === "hijri" 
            ? this.formattedHijriValue 
            : this.formattedGregorianValue;
    }
    
    get inputPlaceholder() {
        if (this.props.placeholder) return this.props.placeholder;
        const formatStr = localization.dateFormat || "yyyy-MM-dd";
        return getPlaceholderForFormat(formatStr, this.state.currentMode, this.props.showTime);
    }
    
    get modeToggleTitle() {
        return this.state.currentMode === "hijri" 
            ? "التحويل للميلادي" 
            : "التحويل للهجري";
    }
    
    get helperText() {
        if (!this.currentValue) return "";
        return this.state.currentMode === "hijri"
            ? `الميلادي: ${this.formattedGregorianValue} م`
            : `الهجري: ${this.formattedHijriValue} هـ`;
    }
    
    toggleCalendarMode() {
        this.state.currentMode = this.state.currentMode === "hijri" ? "gregorian" : "hijri";
        this.initPickerFromValue();
    }
    
    setMode(mode) {
        this.state.currentMode = mode;
        this.initPickerFromValue();
    }
    
    togglePicker() {
        this.state.showPicker = !this.state.showPicker;
        if (this.state.showPicker) {
            this.initPickerFromValue();
        }
    }
    
    closePicker() {
        this.state.showPicker = false;
    }
    
    onInputFocus() {
        this.state.showPicker = true;
        this.initPickerFromValue();
    }
    
    onInputChange(ev) {
        const val = ev.target.value;
        const parsed = parseDateString(val, this.state.currentMode);
        if (parsed) {
            this.setValue(parsed);
        } else if (val === "") {
            this.setValue(null);
        }
        ev.target.value = this.inputValue;
    }
    
    onMonthSelect(ev) {
        this.state.pickerMonth = parseInt(ev.target.value, 10);
    }
    
    onYearSelect(ev) {
        this.state.pickerYear = parseInt(ev.target.value, 10);
    }
    
    prevMonth() {
        if (this.state.pickerMonth === 1) {
            this.state.pickerMonth = 12;
            this.state.pickerYear--;
        } else {
            this.state.pickerMonth--;
        }
    }
    
    nextMonth() {
        if (this.state.pickerMonth === 12) {
            this.state.pickerMonth = 1;
            this.state.pickerYear++;
        } else {
            this.state.pickerMonth++;
        }
    }
    
    isSelectedDay(day) {
        const val = this.currentValue;
        if (!val) return false;
        
        if (this.state.currentMode === "hijri") {
            const h = gregorianToHijri(val);
            return h && h.y === this.state.pickerYear && h.m === this.state.pickerMonth && h.d === day;
        } else {
            return val.getUTCFullYear() === this.state.pickerYear && (val.getUTCMonth() + 1) === this.state.pickerMonth && val.getUTCDate() === day;
        }
    }
    
    selectDay(day) {
        let gDate;
        if (this.state.currentMode === "hijri") {
            gDate = hijriToGregorian(this.state.pickerYear, this.state.pickerMonth, day);
        } else {
            gDate = new Date(Date.UTC(this.state.pickerYear, this.state.pickerMonth - 1, day));
        }
        
        if (gDate) {
            gDate.setUTCHours(parseInt(this.state.pickerHour, 10));
            gDate.setUTCMinutes(parseInt(this.state.pickerMinute, 10));
            this.setValue(gDate);
        }
        if (!this.props.showTime) {
            this.closePicker();
        }
    }
    
    onTimeChange() {
        const val = this.currentValue || new Date();
        let gDate;
        if (this.state.currentMode === "hijri") {
            const h = gregorianToHijri(val);
            gDate = h ? hijriToGregorian(this.state.pickerYear, this.state.pickerMonth, h.d) : val;
        } else {
            gDate = new Date(Date.UTC(this.state.pickerYear, this.state.pickerMonth - 1, val.getUTCDate()));
        }
        
        if (gDate) {
            gDate.setUTCHours(parseInt(this.state.pickerHour, 10));
            gDate.setUTCMinutes(parseInt(this.state.pickerMinute, 10));
            this.setValue(gDate);
        }
    }
    
    selectToday() {
        const today = new Date();
        this.setValue(today);
        this.closePicker();
    }
    
    setValue(utcDate) {
        if (!utcDate) {
            this.props.record.update({ [this.props.name]: false });
            return;
        }
        
        const { DateTime } = window.luxon;
        const newDateTime = DateTime.fromObject({
            year: utcDate.getUTCFullYear(),
            month: utcDate.getUTCMonth() + 1,
            day: utcDate.getUTCDate(),
            hour: this.props.showTime ? utcDate.getUTCHours() : 0,
            minute: this.props.showTime ? utcDate.getUTCMinutes() : 0,
        });
        
        this.props.record.update({ [this.props.name]: newDateTime });
    }
    
    formatNumber(num) {
        return String(num).padStart(2, "0");
    }
    
    get hoursList() {
        const hours = [];
        for (let i = 0; i < 24; i++) hours.push(i);
        return hours;
    }
    
    get minutesList() {
        const minutes = [];
        for (let i = 0; i < 60; i++) minutes.push(i);
        return minutes;
    }
    
    get monthsList() {
        return this.state.currentMode === 'hijri' ? HIJRI_MONTHS : GREGORIAN_MONTHS;
    }
    
    get daysOfWeek() {
        return this.state.currentMode === 'hijri' 
            ? ['ح', 'ن', 'ث', 'ر', 'خ', 'ج', 'س']
            : ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
    }
    
    get yearsList() {
        const list = [];
        const min = this.state.currentMode === 'hijri' ? 1350 : 1930;
        const max = this.state.currentMode === 'hijri' ? 1500 : 2080;
        for (let y = min; y <= max; y++) {
            list.push(y);
        }
        return list;
    }
    
    get gridPaddingDays() {
        let dayOfWeek = 0;
        if (this.state.currentMode === 'hijri') {
            const gFirst = hijriToGregorian(this.state.pickerYear, this.state.pickerMonth, 1);
            if (gFirst) {
                dayOfWeek = gFirst.getUTCDay();
            }
        } else {
            const gFirst = new Date(Date.UTC(this.state.pickerYear, this.state.pickerMonth - 1, 1));
            dayOfWeek = gFirst.getUTCDay();
        }
        const pads = [];
        for (let i = 0; i < dayOfWeek; i++) {
            pads.push(i);
        }
        return pads;
    }
    
    get gridDays() {
        let numDays = 30;
        if (this.state.currentMode === 'hijri') {
            numDays = getDaysInHijriMonth(this.state.pickerYear, this.state.pickerMonth);
        } else {
            numDays = new Date(Date.UTC(this.state.pickerYear, this.state.pickerMonth, 0)).getUTCDate();
        }
        const days = [];
        for (let d = 1; d <= numDays; d++) {
            days.push(d);
        }
        return days;
    }
}

export const hijriDateField = {
    component: HijriDateField,
    displayName: _t("Hijri Date"),
    supportedTypes: ["date", "datetime"],
    extractProps: ({ attrs, options, field }, dynamicInfo) => ({
        readonly: dynamicInfo.readonly,
        required: dynamicInfo.required,
        placeholder: attrs.placeholder,
        showTime: field.type === "datetime",
    }),
};

registry.category("fields").add("hijri_date", hijriDateField);
