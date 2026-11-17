# UI/UX Engineering & Design Standards
## Production-Grade UI/UX Principles with Tailwind CSS & Prebuilt Components

This document outlines the UI/UX rules used by senior designers and developers, tailored for healthcare applications (**Swasthya-Sewa**). It also defines the **prebuilt component library** stack compatible with **Tailwind CSS and HTMX**.

---

## 1. Senior UI/UX Core Rules & Laws

### Rule 1.1: The "Four States" Rule for Every Screen
A senior engineer never designs just the "happy path" (when data exists). Every interactive screen and component **must** account for four distinct states:
1. **Loading State:** Instant visual feedback (spinner or skeleton loader) when an HTMX request is in flight. Never leave the user wondering if their click registered.
2. **Empty State:** Friendly, actionable illustration/message when no records exist (e.g., *"No appointments booked yet. Find a doctor to get started."* with a direct CTA button).
3. **Error State:** Clear, human-readable error banners (e.g., *"This slot was just claimed. Please pick another."*) with non-destructive recovery actions.
4. **Success State:** Clear visual confirmation (e.g., green checkmark toast, booking receipt pass with appointment ID).

---

### Rule 1.2: Affordance & Instant HTMX Feedback
In an HTMX application, network requests happen in the background. Senior developers use HTMX indicators to prevent double-clicks:
```html
<!-- Submit button automatically disables and shows spinner while request is processing -->
<button type="submit" 
        class="btn btn-primary flex items-center gap-2"
        hx-indicator="#loading-spinner">
    <span>Confirm & Pay</span>
    <span id="loading-spinner" class="htmx-indicator loading loading-spinner loading-sm"></span>
</button>
```

---

### Rule 1.3: Visual Hierarchy & Trust Signals for Healthcare
* **Color Psychology in Healthcare:**
  * **Primary (Trust & Clinical Authority):** Deep Medical Blue (`#0284c7` / `sky-600` or `indigo-600`) or Teal (`teal-600`).
  * **Success / Available:** Emerald Green (`emerald-600`). Signifies confirmed appointments and open slots.
  * **Warning / Temporary Hold:** Amber (`amber-500`). Used for the 10-minute payment countdown.
  * **Danger / Urgent:** Rose (`rose-600`). Used for cancellations and critical warnings.
* **Trust Badges:** Always highlight doctor verification:
  * NMC Verified Badge (`<span class="badge badge-success gap-1">✓ NMC Verified</span>`).
  * Transparent consultation fees upfront before opening the slot picker.

---

### Rule 1.4: Multi-Step Booking Clarity (The Stepper Pattern)
Never overwhelm patients with a massive single-page form. Break the appointment journey into visible steps:
$$\text{1. Select Doctor} \longrightarrow \text{2. Choose Available Slot} \longrightarrow \text{3. Pay (eSewa / Khalti)} \longrightarrow \text{4. Video Call / Clinic Pass}$$

---

## 2. Recommended Prebuilt Component Stack (Zero React / SPA Overhead)

For pure HTML + Tailwind CSS + HTMX, the gold-standard prebuilt libraries are:

### Library 1: **DaisyUI** (Primary Recommendation)
* **What is it?** The most popular semantic component library for Tailwind CSS.
* **Why it's perfect for HTMX:** It requires **zero JavaScript libraries** or React wrappers! It provides clean semantic classes like `btn`, `card`, `badge`, `modal`, `steps`, `alert`, and `table` built purely on Tailwind.
* **Setup via CDN:**
  ```html
  <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css" rel="stylesheet" type="text/css" />
  <script src="https://cdn.tailwindcss.com"></script>
  ```

### Library 2: **Flowbite / Preline UI** (For Interactive Modals & Drawers)
* Provides accessible Tailwind HTML templates for date pickers, dropdowns, and toast notifications.

### Library 3: **Lucide Icons**
* Crisp, modern SVG icons for healthcare (stethoscope, calendar, video, credit card, clock, check-circle).
* Included via standard `<svg>` or Lucide CDN.

---

## 3. Production-Ready Prebuilt Component Snippets

### 3.1 Doctor Profile Card (DaisyUI + Tailwind)

```html
<div class="card card-side bg-base-100 shadow-md hover:shadow-xl transition-all border border-slate-200 rounded-2xl overflow-hidden">
  <figure class="w-48 bg-slate-100 relative">
    <img src="{{ doctor.avatar_url|default:'/static/img/default-avatar.png' }}" 
         alt="{{ doctor.user.full_name }}" 
         class="h-full w-full object-cover" />
    {% if doctor.is_verified %}
      <span class="badge badge-success text-xs font-semibold gap-1 absolute top-3 left-3 shadow">
        <svg class="w-3 h-3 fill-current" viewBox="0 0 20 20"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/></svg>
        NMC Verified
      </span>
    {% endif %}
  </figure>
  
  <div class="card-body p-6 flex-1">
    <div class="flex justify-between items-start">
      <div>
        <h2 class="card-title text-xl font-bold text-slate-800">Dr. {{ doctor.user.full_name }}</h2>
        <p class="text-sm text-sky-600 font-medium">{{ doctor.department }} • {{ doctor.years_of_experience }} Years Exp.</p>
      </div>
      <div class="text-right">
        <span class="text-xs text-slate-500 uppercase tracking-wider block">Consultation Fee</span>
        <span class="text-lg font-bold text-slate-900">NPR {{ doctor.fee_physical }}</span>
      </div>
    </div>
    
    <p class="text-slate-600 text-sm line-clamp-2 my-2">{{ doctor.bio }}</p>
    
    <div class="card-actions justify-end mt-4">
      <a href="{% url 'doctor_detail' doctor.id %}" class="btn btn-outline btn-primary btn-sm rounded-lg">
        View Schedule
      </a>
      <button class="btn btn-primary btn-sm rounded-lg"
              hx-get="{% url 'doctor_slots_modal' doctor.id %}"
              hx-target="#modal-container"
              hx-swap="innerHTML">
        Book Appointment
      </button>
    </div>
  </div>
</div>
```

---

### 3.2 Dynamic Slot Picker Grid (Color-Coded Statuses)

```html
<div class="p-6 bg-white rounded-2xl border border-slate-200">
  <h3 class="text-base font-semibold text-slate-800 mb-4 flex items-center justify-between">
    <span>Available Time Slots ({{ selected_date|date:"M d, Y" }})</span>
    <span class="text-xs text-slate-500 font-normal">20 min per consultation</span>
  </h3>

  <!-- Slot Grid -->
  <div class="grid grid-cols-3 sm:grid-cols-4 gap-3">
    {% for slot in slots %}
      {% if slot.status == 'AVAILABLE' %}
        <button type="button"
                hx-post="{% url 'hold_appointment_slot' %}"
                hx-vals='{"doctor_id": "{{ doctor.id }}", "date": "{{ selected_date }}", "time": "{{ slot.start_time }}"}'
                hx-target="#checkout-modal"
                class="py-3 px-4 rounded-xl border-2 border-emerald-500 text-emerald-700 bg-emerald-50 hover:bg-emerald-600 hover:text-white transition-all font-semibold text-sm shadow-sm flex flex-col items-center justify-center">
          <span>{{ slot.start_time|time:"h:i A" }}</span>
          <span class="text-[10px] font-normal uppercase tracking-wider mt-0.5">Available</span>
        </button>
      {% elif slot.status == 'HELD' %}
        <button disabled 
                class="py-3 px-4 rounded-xl border border-amber-300 bg-amber-50 text-amber-700 opacity-80 cursor-not-allowed text-sm flex flex-col items-center justify-center">
          <span>{{ slot.start_time|time:"h:i A" }}</span>
          <span class="text-[10px] uppercase tracking-wider mt-0.5">In Checkout</span>
        </button>
      {% else %}
        <button disabled 
                class="py-3 px-4 rounded-xl border border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed text-sm flex flex-col items-center justify-center">
          <span>{{ slot.start_time|time:"h:i A" }}</span>
          <span class="text-[10px] uppercase tracking-wider mt-0.5">Booked</span>
        </button>
      {% endif %}
    {% empty %}
      <div class="col-span-full py-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
        <p class="text-slate-500 font-medium">Dr. {{ doctor.user.full_name }} is not available on this date.</p>
        <p class="text-xs text-slate-400 mt-1">Please pick another date from the calendar above.</p>
      </div>
    {% endfor %}
  </div>
</div>
```

---

### 3.3 eSewa & Khalti Payment Checkout Modal (DaisyUI Modal)

```html
<dialog id="payment_modal" class="modal modal-open">
  <div class="modal-box max-w-md rounded-2xl p-6">
    <h3 class="font-bold text-lg text-slate-800">Complete Your Booking</h3>
    
    <!-- 10-Minute Expiry Countdown -->
    <div class="alert alert-warning py-2 px-3 rounded-xl mt-3 text-xs flex items-center justify-between">
      <span>Slot held temporarily for:</span>
      <span class="font-mono font-bold text-sm" id="countdown-timer">09:59</span>
    </div>

    <!-- Booking Summary Card -->
    <div class="bg-slate-50 rounded-xl p-4 my-4 text-sm space-y-1.5 border border-slate-200">
      <div class="flex justify-between"><span class="text-slate-500">Doctor:</span> <span class="font-semibold text-slate-800">Dr. {{ appointment.doctor.user.full_name }}</span></div>
      <div class="flex justify-between"><span class="text-slate-500">Date & Time:</span> <span class="font-semibold text-slate-800">{{ appointment.appointment_date }} at {{ appointment.start_time }}</span></div>
      <div class="flex justify-between"><span class="text-slate-500">Consultation Type:</span> <span class="badge badge-outline badge-sm">{{ appointment.get_consultation_type_display }}</span></div>
      <div class="divider my-1"></div>
      <div class="flex justify-between text-base font-bold text-slate-900"><span>Total Payable:</span> <span>NPR {{ appointment.doctor.fee_physical }}</span></div>
    </div>

    <!-- Payment Gateway Options -->
    <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Select Payment Method</p>
    <div class="grid grid-cols-2 gap-3 mb-6">
      <!-- eSewa Option -->
      <a href="{% url 'initiate_esewa_payment' appointment.id %}" 
         class="border-2 border-emerald-500 hover:bg-emerald-50 p-4 rounded-xl flex flex-col items-center justify-center transition-all group">
        <span class="text-base font-bold text-emerald-600 group-hover:scale-105 transition-transform">eSewa</span>
        <span class="text-[11px] text-slate-500 mt-1">Digital Wallet</span>
      </a>

      <!-- Khalti Option -->
      <a href="{% url 'initiate_khalti_payment' appointment.id %}" 
         class="border-2 border-purple-500 hover:bg-purple-50 p-4 rounded-xl flex flex-col items-center justify-center transition-all group">
        <span class="text-base font-bold text-purple-600 group-hover:scale-105 transition-transform">Khalti</span>
        <span class="text-[11px] text-slate-500 mt-1">Digital Wallet</span>
      </a>
    </div>

    <div class="modal-action mt-0">
      <button class="btn btn-ghost btn-sm text-slate-500" onclick="document.querySelector('#payment_modal').remove()">Cancel</button>
    </div>
  </div>
</dialog>
```

---

### 3.4 Out-of-Band (OOB) Toast Notification for HTMX

When any HTMX action succeeds (e.g. profile saved, appointment cancelled), the server returns the main content **plus** an out-of-band toast alert that injects itself into the fixed toast container:

```html
<!-- Server returns this snippet in the response -->
<div id="toast-container" hx-swap-oob="beforeend">
  <div class="alert alert-success shadow-lg rounded-xl flex items-center justify-between py-3 px-4 mb-2 animate-bounce">
    <div class="flex items-center gap-2">
      <svg class="w-5 h-5 fill-current text-white" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
      <span class="text-sm font-semibold text-white">Appointment successfully confirmed!</span>
    </div>
    <button onclick="this.parentElement.remove()" class="text-white hover:text-slate-200 text-sm font-bold">✕</button>
  </div>
</div>
```

---

## 4. Summary of Frontend Libraries Configured

| Component | Library | Delivery Method |
| :--- | :--- | :--- |
| **CSS Framework** | **Tailwind CSS 3.x** | CDN (`cdn.tailwindcss.com`) |
| **Prebuilt Components** | **DaisyUI 4.x** | CDN (`cdn.jsdelivr.net/.../daisyui@4/full.min.css`) |
| **Interactivity & Swaps** | **HTMX 1.9.x** | CDN (`unpkg.com/htmx.org`) |
| **Micro-Interactions (Dropdowns/Modals)** | **Alpine.js 3.x** | CDN (`unpkg.com/alpinejs`) |
| **Icons** | **Lucide Icons** | SVG inline snippets or CDN |

All of these libraries load via lightweight CDN links directly in your base template (`templates/base.html`), requiring zero Webpack, Node.js, or complex frontend build pipelines.
